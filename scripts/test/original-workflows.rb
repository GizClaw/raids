# Product boundary: originals are the exact local origin/main blobs. This check
# is read-only/offline and deliberately never fetches or updates that reference.
require 'open3'
raids = Dir['workflows/{story,adventure,learn}-*'] + %w[workflows/murder-mystery workflows/chat-assistant workflows/journey-guide]
count = 0
raids.sort.each do |package|
  listing, status = Open3.capture2('git', 'ls-tree', '-r', '--name-only', 'origin/main', package)
  abort "cannot read origin/main inventory for #{package}" unless status.success?
  listing.lines.map(&:strip).grep(/\.yaml\z/).each do |file|
    original, status = Open3.capture2('git', 'show', "origin/main:#{file}")
    abort "#{file}: original differs from origin/main" unless status.success? && File.binread(file) == original.b
    count += 1
  end
end
puts "validated #{count} byte-identical original Workflow/test files in #{raids.size} raids"
