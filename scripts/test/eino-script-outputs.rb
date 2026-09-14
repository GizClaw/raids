require 'yaml'

# A small lexical check, not a script evaluator. Inspect return {...} literals
# in every language, ignoring comments/string contents and nested value keys.
module EinoScriptOutputs
  TOKEN = /\s+|\#.*?$|\/\/.*?$|\/\*.*?\*\/|""".*?"""|'''.*?'''|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|`(?:\\.|[^`\\])*`|[A-Za-z_$][\w$]*|./m

  def self.return_keys(source)
    tokens = source.scan(TOKEN).reject { |t| t.match?(/\A\s/) || t.start_with?('#', '//', '/*') }
    keys = []
    tokens.each_index do |i|
      next unless tokens[i] == 'return'
      j = i + 1
      j += 1 while tokens[j] == '('
      next unless tokens[j] == '{'
      stack = ['{']
      key_position = true
      j += 1
      while j < tokens.size && !stack.empty?
        token = tokens[j]
        if stack.size == 1 && key_position
          if tokens[j + 1] == ':'
            keys << (token.start_with?('"', "'") ? token[1...-1] : token)
          end
          key_position = false
        end
        if ['{', '[', '('].include?(token)
          stack << token
        elsif ['}', ']', ')'].include?(token)
          stack.pop
        elsif token == ',' && stack.size == 1
          key_position = true
        end
        j += 1
      end
    end
    keys.uniq
  end

  def self.errors(document, file)
    document.fetch('spec').fetch('eino').fetch('graph').fetch('nodes').flat_map do |node|
      next [] unless node['type'] == 'script'
      extra = return_keys(node.fetch('source')) - node.fetch('outputs', {}).keys
      extra.map { |key| "#{file}: #{node.fetch('id')} (#{node['language']}): undeclared returned output #{key.inspect}" }
    end
  end
end

if $PROGRAM_NAME == __FILE__
  files = ARGV.empty? ? Dir['workflows/*/eino*.yaml'].sort : ARGV
  abort 'no Eino workflows found' if files.empty?
  errors = files.flat_map { |file| EinoScriptOutputs.errors(YAML.load_file(file), file) }
  abort errors.join("\n") unless errors.empty?
  puts "validated script return outputs in #{files.size} Eino workflows"
end
