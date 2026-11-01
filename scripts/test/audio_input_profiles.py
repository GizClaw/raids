"""Select native Lite PTT input in task-owned test resources.

This changes Model/Profile selection, never a story Graph. Complex Eino Graphs
currently use native Model transcription before their text-dependent logic;
callers must inspect provider payloads before claiming direct audio reasoning.
"""

from __future__ import annotations

from copy import deepcopy


def native_lite_model(source: dict, identifier: str) -> dict:
    model = deepcopy(source)
    data = model["spec"]["provider_data"]
    if data.get("upstream_model") != "doubao-seed-2-1-lite-260915":
        raise ValueError("native speech tests require the selected Seed 2.1 Lite revision")
    if data.get("api_mode") != "chat_completions":
        raise ValueError("native speech tests require the existing Ark chat-completions path")
    model["metadata"]["id"] = identifier
    data["support_text_only"] = False
    data["default_thinking_level"] = "disabled"
    return model


def native_ptt_profile(source: dict, workflows: list[str], models: dict[str, str]) -> dict:
    profile = deepcopy(source)
    spec = profile["spec"]
    for alias in workflows:
        binding = spec["workflows"][alias]
        binding.pop("ptt_asr_model", None)
        binding.pop("realtime_asr_model", None)
    for alias, identifier in models.items():
        spec["resources"]["models"][alias]["resource_id"] = identifier
    return profile


def ptt_workflow(source: dict, identifier: str) -> dict:
    """Leave input selection to the test Profile, without changing the Graph.

    Older resources name ASR inside voice_adapter. That reference is validated
    even when the Profile selects native input, so omit it in the private copy.
    The baseline still explicitly selects ASR in its own Profile.
    """
    workflow = deepcopy(source)
    workflow["metadata"]["id"] = identifier
    workflow["spec"]["eino"].get("voice_adapter", {}).pop("asr_model", None)
    return workflow


def speech_host_turns(source: dict, voice: str, client: str = "host") -> dict:
    """Speak generated player input, preserving the original response guards.

    Player/judge turns stay text. Original intended text remains in the test
    document; it is not sent as a caption beside the host's audio.
    """
    document = deepcopy(source)
    steps = []
    for step in document["steps"]:
        stream = step.get("peer_stream")
        if step.get("client") != client or not stream or stream.get("mode") != "text":
            steps.append(step)
            continue
        identifier = step["id"]
        audio = identifier + "_spoken_input"
        document["variables"][audio] = {
            "direction": "output", "type": "audio", "max_bytes": 16777216,
            "media_type": "audio/ogg", "codec": "opus",
        }
        steps.append({
            "id": "speak_" + identifier, "client": client, "timeout": "2m",
            "speech": {
                "method": "server.speech.synthesize", "cache": "run",
                "request": {"voice_name": voice, "text": stream["input"],
                            "accepted_content_types": ["audio/ogg"]},
            },
            "save_as": audio,
        })
        stream.update(mode="push-to-talk", input="${" + audio + "}", pacing="20ms")
        transcript = identifier + "_input_transcript"
        capture = step.setdefault("capture", {})
        if "/transcript" not in capture.values():
            document["variables"][transcript] = {"direction": "output", "type": "string"}
            capture[transcript] = "/transcript"
            steps.append(step)
            steps.append({"id": "emit_" + transcript, "output": {"variable": transcript}})
            continue
        steps.append(step)
    document["steps"] = steps
    return document
