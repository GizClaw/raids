require 'yaml'
require 'json'
# Walk all workflow documents, including nested graphs and every Tester variant.
scripts = []
walk = lambda do |value, file, path|
  case value
  when Hash
    if value['type'] == 'script' && value['language'] == 'starlark'
      scripts << {file: file, path: path, source: value.fetch('source'), entrypoint: value['entrypoint']}
    end
    value.each { |key, child| walk.call(child, file, "#{path}/#{key}") }
  when Array
    value.each_with_index { |child, i| walk.call(child, file, "#{path}/#{i}") }
  end
end
Dir['workflows/**/*.yaml'].sort.each { |file| walk.call(YAML.load_file(file), file, '') }
puts JSON.generate(scripts)
