"""Run shipped Raids resources on isolated, released GizClaw + real providers."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import shlex
import shutil
import subprocess
import tempfile
import time
import zipfile

import yaml

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
IMAGE = "ghcr.io/gizclaw/gizclaw@sha256:122619e0ecc54e2fc7b3718f6ba08148ce868b7f3890b3ff9ee993ea271f5df5"
REQUIRED = ["GIZCLAW_VOLC_" + suffix for suffix in
            ["SPEECH_APP_ID", "SPEECH_API_KEY", "ARK_API_KEY", "SEARCH_API_KEY", "OPENAPI_ACCESS_KEY_ID", "OPENAPI_ACCESS_KEY"]]


def credentials(path):
    result = {}
    for line in Path(path).read_text().splitlines():
        key, separator, value = line.removeprefix("export ").partition("=")
        if separator and key.strip() in REQUIRED:
            parts = shlex.split(value, comments=True)
            if len(parts) == 1:
                result[key.strip()] = parts[0]
    missing = [key for key in REQUIRED if not result.get(key)]
    if missing:
        raise SystemExit("Missing provider credentials: " + ", ".join(missing))
    return result


def resources():
    # Apply the public profiles' complete real closure, with no graph or alias rewrites.
    documents = {}
    for directory in ["credentials", "tenants", "models", "voices", "memory-layouts", "tools", "workflows"]:
        for path in (ROOT / directory).rglob("*.yaml"):
            doc = yaml.safe_load(path.read_text())
            documents[(doc["kind"], doc["metadata"]["id"])] = doc
    selected = set()
    profiles = [yaml.safe_load((ROOT / "runtime-profiles" / (name + ".yaml")).read_text()) for name in ["default", "testing"]]
    for profile in profiles:
        spec = profile["spec"]
        for binding in spec["workflows"].values():
            selected.add(("Workflow", binding["resource_id"]))
        for kind, group in [("Model", "models"), ("Voice", "voices"), ("Tool", "tools")]:
            for binding in spec["resources"].get(group, {}).values():
                if binding.get("resource_id"):
                    selected.add((kind, binding["resource_id"]))
        for binding in spec["resources"].get("memories", {}).values():
            selected.add(("MemoryLayout", binding["layout_id"]))
    for kind, identifier in list(selected):
        provider = documents[(kind, identifier)]["spec"].get("provider")
        if isinstance(provider, dict) and provider.get("kind", "").endswith("-tenant"):
            tenant_kind = "".join(part.capitalize() for part in provider["kind"].split("-"))
            selected.add((tenant_kind, provider["id"]))
    for kind, identifier in list(selected):
        if kind.endswith("Tenant"):
            selected.add(("Credential", documents[(kind, identifier)]["spec"]["credential_id"]))
    order = ["Credential", "Tenant", "Model", "Voice", "MemoryLayout", "Tool", "Workflow"]
    items = [documents[key] for key in sorted(selected, key=lambda key: (order.index("Tenant" if key[0].endswith("Tenant") else key[0]), key[1]))]
    items += profiles
    items += [yaml.safe_load((ROOT / "registration-tokens" / (name + ".yaml")).read_text()) for name in ["default", "testing"]]
    return {"apiVersion": "gizclaw.admin/v1alpha1", "kind": "ResourceList", "spec": {"items": items}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--credential-file", default=os.environ.get("RAIDS_CHAT_E2E_CREDENTIAL_FILE"))
    parser.add_argument("--repeat", type=int, default=3)
    parser.add_argument("--parallel", type=int, default=3)
    parser.add_argument("--filter", default="")
    parser.add_argument("--standard", choices=["none", "smoke", "quality", "soak", "all"], default="all")
    args = parser.parse_args()
    if not args.credential_file:
        parser.error("--credential-file or RAIDS_CHAT_E2E_CREDENTIAL_FILE is required")
    if args.repeat < 1 or args.parallel < 1:
        parser.error("repeat and parallel must be positive")
    env = dict(os.environ, **credentials(args.credential_file))
    env["GIZCLAW_MEM0_API_KEY"] = secrets.token_hex(24)
    env["GIZCLAW_MEM0_ENDPOINT"] = "http://mem0:8000"
    project = "raids-chat-" + secrets.token_hex(5)
    state = Path(tempfile.mkdtemp(prefix=project + "-"))
    report = ROOT / "tests/giztest/reports" / project
    report.mkdir(parents=True)
    env.update(RAIDS_CHAT_E2E_STATE=str(state), RAIDS_CHAT_E2E_REPO=str(ROOT), RAIDS_CHAT_E2E_REPORT=str(report))
    compose = ["docker", "compose", "--project-name", project, "--file", str(HERE / "compose.yaml")]
    audit = {"project": project, "runtime_image": IMAGE, "parameters": vars(args) | {"credential_file": "provided in process; not recorded"}, "checks": {}}
    audit["source_sha256"] = {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(set([ROOT / "runtime-profiles/default.yaml", ROOT / "runtime-profiles/testing.yaml",
                                ROOT / "workflows/chat-assistant/eino.yaml",
                                ROOT / "scripts/test/chat-assistant/cmd/e2e-init/main.go", *HERE.glob("*")]))
        if path.is_file()
    }

    def run(command, log, **kwargs):
        with (report / log).open("a") as output:
            result = subprocess.run(command, cwd=ROOT, env=env, stdout=output, stderr=subprocess.STDOUT, **kwargs)
        if result.returncode:
            # Provider values are never printed by the harness.
            raise RuntimeError(f"{log}: command failed with exit {result.returncode}")

    def cli(*command, log="cli.log", **kwargs):
        run(compose + ["exec", "-T", "cli", "/usr/bin/gizclaw", *command], log, **kwargs)

    try:
        arch = subprocess.check_output(["docker", "info", "--format", "{{.Architecture}}"], text=True).strip()
        build_env = dict(env, CGO_ENABLED="0", GOOS="linux", GOARCH="arm64" if arch in ["aarch64", "arm64"] else "amd64")
        with (report / "build.log").open("w") as output:
            subprocess.run(["go", "build", "-mod=readonly", "-o", str(state / "e2e-init"), "./cmd/e2e-init"],
                           cwd=ROOT / "scripts/test/chat-assistant", env=build_env, stdout=output, stderr=subprocess.STDOUT, check=True)
        run(["docker", "run", "--rm", "--network", "none", "--entrypoint", "/init", "--mount", f"type=bind,source={state},target=/state",
             "--mount", f"type=bind,source={state / 'e2e-init'},target=/init,readonly",
             "--mount", f"type=bind,source={HERE},target=/templates,readonly", IMAGE, "/state", "/templates"], "init.log")
        closure = resources()
        resource_json = json.dumps(closure, ensure_ascii=False)
        (state / "resources.json").write_text(resource_json)
        audit["resource_closure_sha256"] = hashlib.sha256(resource_json.encode()).hexdigest()
        from generate import generate
        count = generate(state / "tests", repeat=args.repeat, case_filter=args.filter)
        with zipfile.ZipFile(report / "giztest-inputs.zip", "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted((state / "tests").glob("*.yaml")):
                archive.write(path, path.name)
        print(f"{project}: {len(closure['spec']['items'])} shipped Resources; {count} generated device scenarios", flush=True)
        run(compose + ["up", "--detach", "--wait", "--wait-timeout", "300", "cli"], "startup.log")
        # Server and Edge use the exact released binary. Readiness goes through its HTTP endpoint.
        for service, port in [("server", 9820), ("edge", 9821)]:
            for attempt in range(90):
                result = subprocess.run(compose + ["exec", "-T", "mem0", "python", "-c",
                    f"import urllib.request; urllib.request.urlopen('http://{service}:{port}/server-info',timeout=2).read()"],
                    cwd=ROOT, env=env, capture_output=True)
                if result.returncode == 0:
                    break
                time.sleep(1)
            else:
                raise RuntimeError(service + " did not become ready")
        cli("--version", log="runtime-version.log")
        cli("admin", "apply", "--context", "raids-e2e", "-f", "/state/resources.json", log="apply.log")
        audit["checks"]["resource_apply"] = "PASS"
        cli("test", "validate", "-f", "/state/tests", log="validate.log")
        if count:
            cli("test", "run", "--parallel", str(args.parallel), "--evidence", "full",
                "--output", "/reports/tools.json", "/state/tests", log="tools.log")
            audit["checks"]["device_tools"] = "PASS"
        if args.standard != "none":
            tiers = ["smoke", "quality", "soak"] if args.standard == "all" else [args.standard]
            for tier in tiers:
                print(f"{project}: running standard Chat {tier}", flush=True)
                run(compose + ["exec", "-T", "-e", "GIZCLAW_TEST_REGISTRATION_TOKEN=9c845896-1447-5a7e-b799-a1df42694fb8",
                    "cli", "/usr/bin/gizclaw", "test", "run", "--parallel", "1", "--evidence", "full",
                    "--output", f"/reports/{tier}.json", f"/raids/tests/giztest/{tier}/chat-assistant.eino.giztest.yaml"], tier + ".log")
                audit["checks"][tier] = "PASS"
        if audit["resource_closure_sha256"] != hashlib.sha256(json.dumps(resources(), ensure_ascii=False).encode()).hexdigest():
            raise RuntimeError("shipped Resources changed during this E2E run")
        for path, digest in audit["source_sha256"].items():
            if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != digest:
                raise RuntimeError("E2E input changed during this run: " + path)
        audit["status"] = "PASS"
    except Exception as error:
        audit["status"] = "FAIL"
        audit["error"] = str(error)
        print(f"{project}: {error}", flush=True)
    finally:
        result = subprocess.run(compose + ["logs", "--no-color"], cwd=ROOT, env=env, capture_output=True, text=True)
        logs = result.stdout
        for key in REQUIRED + ["GIZCLAW_MEM0_API_KEY"]:
            if env.get(key):
                logs = logs.replace(env[key], "[REDACTED]")
        (report / "containers.log").write_text(logs)
        subprocess.run(compose + ["down", "--volumes", "--remove-orphans"], cwd=ROOT, env=env, capture_output=True)
        remaining = subprocess.check_output(["docker", "ps", "-aq", "--filter", "label=com.docker.compose.project=" + project], text=True).strip()
        networks = subprocess.check_output(["docker", "network", "ls", "-q", "--filter", "label=com.docker.compose.project=" + project], text=True).strip()
        volumes = subprocess.check_output(["docker", "volume", "ls", "-q", "--filter", "label=com.docker.compose.project=" + project], text=True).strip()
        audit["cleanup"] = "PASS" if not (remaining or networks or volumes) else "FAIL"
        (report / "audit.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n")
        shutil.rmtree(state)
        print(f"Evidence: {report}; status={audit['status']}; cleanup={audit['cleanup']}", flush=True)
    raise SystemExit(0 if audit["status"] == "PASS" and audit["cleanup"] == "PASS" else 1)


if __name__ == "__main__":
    main()
