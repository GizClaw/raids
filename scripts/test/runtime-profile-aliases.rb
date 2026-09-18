# GizClaw 0.18.15+ rejects a RuntimeProfile whose collection names, binding keys
# or app_config keys break runtimealias.Validate, but only when a Server
# normalizes it: `gizclaw admin validate` accepts the same file. Mirror the rule
# so a non-conforming alias fails offline instead of at `gizclaw admin apply`.
require_relative 'yaml_compat'

module RuntimeProfileAliases
  # pkgs/gizclaw/runtimealias/alias.go in GizClaw v0.18.15.
  PATTERN = /\A[a-z0-9]+(?:-[a-z0-9]+)*(?:\.[a-z0-9]+(?:-[a-z0-9]+)*)*\z/
  MAX_BYTES = 63

  module_function

  def valid?(alias_name)
    alias_name.is_a?(String) && alias_name.bytesize <= MAX_BYTES && alias_name.match?(PATTERN)
  end

  # Returns [path, alias] pairs for every alias the Server would reject, plus
  # Workflow aliases bound in more than one collection.
  def errors(spec)
    found = []
    check = ->(path, name) { found << [path, name] unless valid?(name) }
    owners = {}
    (spec.dig('workflows', 'collections') || {}).each do |collection, bindings|
      check.call('workflows.collections', collection)
      (bindings || {}).each_key do |name|
        check.call("workflows.collections.#{collection}", name)
        found << ["workflows.collections.#{collection} (also in #{owners[name]})", name] if owners.key?(name)
        owners[name] ||= collection
      end
    end
    (spec['resources'] || {}).each do |kind, bindings|
      (bindings || {}).each_key { |name| check.call("resources.#{kind}", name) }
    end
    (spec['app_config'] || {}).each_key { |name| check.call('app_config', name) }
    found
  end
end

if $PROGRAM_NAME == __FILE__
  files = Dir.glob('runtime-profiles/*.yaml').sort
  abort 'no RuntimeProfile files found' if files.empty?
  count = 0
  files.each do |file|
    doc = YAML.load_file(file)
    next unless doc['kind'] == 'RuntimeProfile'

    errors = RuntimeProfileAliases.errors(doc.fetch('spec'))
    unless errors.empty?
      errors.each do |path, name|
        warn "#{file}: #{path}: #{name.inspect} must be 1-#{RuntimeProfileAliases::MAX_BYTES} bytes of dot-separated lowercase kebab-case segments"
      end
      exit 1
    end
    count += 1
  end
  puts "validated RuntimeProfile aliases in #{count} files"
end
