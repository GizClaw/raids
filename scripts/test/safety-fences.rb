require_relative 'yaml_compat'

# Check prompt placement, not model compliance. Trace the catalog's published
# models and the Flowcraft draft -> board.getVar -> published script pattern.
module SafetyFences
  FLOWCRAFT_PREFIX = "${board.safety_fence}\n\n".freeze
  # Realtime drivers substitute ${input.safety_fence} in instructions and trim
  # the result, so an off fence leaves no leading blank line. The dotted name
  # is not expanded as an environment variable when manifests are applied.
  REALTIME_PREFIX = "${input.safety_fence}\n\n".freeze
  REALTIME_DRIVERS = %w[doubao-realtime doubao-realtime-duplex dashscope-realtime].freeze
  # ASTTranslate has no system prompt entry, so GizClaw provides no fence.
  UNFENCED_DRIVERS = %w[ast-translate].freeze

  def self.player_file?(file)
    name = File.basename(file)
    !name.start_with?('test') && !name.end_with?('.giztest.yaml') && name.end_with?('.yaml')
  end

  def self.files(root = 'workflows')
    Dir["#{root}/*/*.yaml"].select { |file| player_file?(file) }.sort
  end

  def self.prompt_prefix?(template, format, key)
    key = Regexp.escape(key)
    case format
    when 'f_string'
      template.match?(/\A\{#{key}\}\n\n/)
    when 'go_template'
      template.match?(/\A\{\{\s*\.#{key}\s*\}\}\n\n/) ||
        template.match?(/\A\{\{\s*if\s+\.#{key}\s*\}\}\{\{\s*\.#{key}\s*\}\}\n\n\{\{\s*end\s*\}\}/)
    when 'jinja2'
      template.match?(/\A\{\{\s*#{key}\s*\}\}\n\n/) ||
        template.match?(/\A\{%\s*if\s+#{key}\s*%\}\{\{\s*#{key}\s*\}\}\n\n\{%\s*endif\s*%\}/)
    else
      false
    end
  end

  def self.fenced_prompt?(node)
    system = node.fetch('messages', []).find { |message| message['role'] == 'system' }
    return false unless system
    node.fetch('inputs', {}).any? do |key, binding|
      binding['from'] == 'input.safety_fence' &&
        prompt_prefix?(system.fetch('template', ''), node['format'], key)
    end
  end

  def self.flowcraft_nodes(graph)
    nodes = graph.fetch('nodes')
    publishers = nodes.select { |node| node['type'] == 'script' && node['publish'] == true }
    nodes.select do |node|
      next false unless node['type'] == 'llm' && !node.fetch('config', {})['json_mode']
      output = node.dig('config', 'output_key')
      node['publish'] == true || (output && publishers.any? do |publisher|
        publisher.dig('config', 'source').to_s.match?(/board\.getVar\(\s*["']#{Regexp.escape(output)}["']\s*\)/)
      end)
    end
  end

  def self.eino_nodes(graph)
    nodes = graph.fetch('nodes')
    published = graph.fetch('outputs', []).select { |output| output['mime_type'] == 'text/plain' }.map { |output| output['node'] }
    message_fields = nodes.select { |node| node['type'] == 'chat_model' && published.include?(node['id']) }
                          .map { |node| node.dig('inputs', 'messages', 'from') }.compact
    nodes.select { |node| node['type'] == 'prompt' && message_fields.include?(node.dig('outputs', 'messages')) }
  end

  def self.errors(document, file)
    return [] unless player_file?(file)
    spec = document.fetch('spec')
    driver = spec.fetch('driver')
    return [] if UNFENCED_DRIVERS.include?(driver)
    if REALTIME_DRIVERS.include?(driver)
      return [] if spec.dig(driver.tr('-', '_'), 'instructions').to_s.start_with?(REALTIME_PREFIX)
      return ["#{file}: realtime instructions must start with ${input.safety_fence} followed by a blank line"]
    end
    return ["#{file}: unknown driver #{driver}; review safety fence coverage"] unless %w[eino flowcraft].include?(driver)
    graph = spec.fetch(driver).fetch('graph')
    nodes = driver == 'flowcraft' ? flowcraft_nodes(graph) : eino_nodes(graph)
    return ["#{file}: no player reply prompt found; review the publish path for safety fence coverage"] if nodes.empty?
    nodes.map do |node|
      fenced = driver == 'flowcraft' ? node.dig('config', 'system_prompt').to_s.start_with?(FLOWCRAFT_PREFIX) : fenced_prompt?(node)
      next if fenced
      binding = driver == 'flowcraft' ? '${board.safety_fence}' : 'input.safety_fence with a matching template variable'
      "#{file}: #{node.fetch('id')}: player system prompt must start with #{binding} followed by a blank line"
    end.compact
  end
end

if $PROGRAM_NAME == __FILE__
  files = ARGV.empty? ? SafetyFences.files : ARGV.select { |file| SafetyFences.player_file?(file) }
  abort 'no player workflows found' if files.empty?
  errors = files.flat_map { |file| SafetyFences.errors(YAML.load_file(file), file) }
  abort errors.join("\n") unless errors.empty?
  puts "validated Workspace safety fences in #{files.size} player workflows"
end
