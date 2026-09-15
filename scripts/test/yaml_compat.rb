# Catalog YAML uses anchors and aliases. Psych 4 (Ruby 3.1+) rejects them in
# load/load_file unless asked; older Psych accepts them. Keep both behaviors.
require 'yaml'

if Psych::VERSION.split('.').first.to_i >= 4
  module Psych
    class << self
      alias_method :strict_load, :load
      alias_method :strict_load_file, :load_file

      def load(yaml, **kwargs)
        strict_load(yaml, aliases: true, **kwargs)
      end

      def load_file(filename, **kwargs)
        strict_load_file(filename, aliases: true, **kwargs)
      end
    end
  end
end
