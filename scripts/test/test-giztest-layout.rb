require 'minitest/autorun'
require 'tmpdir'
require_relative 'giztest-layout'

class GiztestCapabilityTest < Minitest::Test
  def text_step
    {'id' => 'response', 'peer_stream' => {'input' => '同一输入', 'require_audio' => false},
     'expect' => {'/text' => {'non_empty' => true}, '/first_text_ms' => {'maximum' => 6000}}}
  end

  def audio_step
    step = text_step
    step['peer_stream']['require_audio'] = true
    step['expect'].merge!('/audio_bytes' => {'minimum' => 1}, '/audio_eos' => {'equals' => true})
    step
  end

  def rejected(&block)
    capture_io { assert_raises(SystemExit, &block) }
  end

  def rpc(client, method = 'register')
    {'id' => "#{client}_#{method}", 'client' => client,
     'rpc' => {'method' => "server.#{method}"}}
  end

  def response(client, timeout = '2m')
    {'id' => "#{client}_response", 'client' => client, 'timeout' => timeout, 'peer_stream' => {}}
  end

  def test_split_references_include_finally_parallel_captures_and_relays
    doc = {'clients' => {'a' => {}}, 'variables' => {'answer' => {'direction' => 'output'}},
           'steps' => [{'id' => 'batch', 'parallel' => [response('a')], 'capture' => {'answer' => '/a_response/text'}}],
           'finally' => [{'id' => 'emit', 'output' => {'variable' => 'answer'}}]}
    GiztestLayout.check_local_references(doc, 'fixture')
    bad = Marshal.load(Marshal.dump(doc)); bad['steps'][0].delete('capture')
    rejected { GiztestLayout.check_local_references(bad, 'fixture') }
    bad = Marshal.load(Marshal.dump(doc)); bad['finally'] << rpc('missing')
    rejected { GiztestLayout.check_local_references(bad, 'fixture') }
    bad = Marshal.load(Marshal.dump(doc)); bad['finally'][0]['output']['variable'] = 'foreign'
    rejected { GiztestLayout.check_local_references(bad, 'fixture') }
    bad = Marshal.load(Marshal.dump(doc)); bad['steps'][0]['parallel'][0]['peer_stream']['input'] = '${foreign}'
    rejected { GiztestLayout.check_local_references(bad, 'fixture') }
    bad = Marshal.load(Marshal.dump(doc)); bad['finally'] << {'id' => 'relay', 'workspace_relay' => {'first_client' => 'a', 'second_client' => 'missing'}}
    rejected { GiztestLayout.check_local_references(bad, 'fixture') }
  end

  def test_speech_requires_registration_on_its_own_client
    speech = {'id' => 'synthesize', 'client' => 'a', 'speech' => {}}
    GiztestLayout.check_speech_order({'steps' => [rpc('a'), speech]}, 'fixture')
    rejected { GiztestLayout.check_speech_order({'steps' => [speech, rpc('a')]}, 'fixture') }
    rejected { GiztestLayout.check_speech_order({'steps' => [rpc('b'), speech]}, 'fixture') }
  end

  def test_idle_gap_includes_finally_and_sums_independent_operations
    doc = {'steps' => [rpc('a'), rpc('b'), response('b'), response('b')],
           'finally' => [rpc('a', 'run.stop')]}
    rejected { GiztestLayout.check_idle_gaps(doc, 'fixture') }
    doc['steps'].delete_at(3)
    GiztestLayout.check_idle_gaps(doc, 'fixture')
  end

  def test_idle_boundary_and_reconnect_do_not_hide_existing_gap
    doc = {'steps' => [rpc('a'), response('b', '3m'), rpc('a', 'run.stop')]}
    GiztestLayout.check_idle_gaps(doc, 'fixture')
    doc['steps'][1]['timeout'] = '181s'
    rejected { GiztestLayout.check_idle_gaps(doc, 'fixture') }
    doc['steps'][2] = {'id' => 'a_reconnect', 'client' => 'a', 'reconnect' => {}}
    rejected { GiztestLayout.check_idle_gaps(doc, 'fixture') }
  end

  def test_parallel_and_relay_count_all_participating_clients
    doc = {'steps' => [rpc('a'), rpc('b'),
      {'id' => 'parallel', 'timeout' => '4m', 'parallel' => [response('a'), response('b')]},
      {'id' => 'relay', 'timeout' => '40m', 'workspace_relay' => {'first_client' => 'a', 'second_client' => 'b'}}],
      'finally' => [rpc('a', 'run.stop'), rpc('b', 'run.stop')]}
    GiztestLayout.check_idle_gaps(doc, 'fixture')
    doc['steps'][2]['parallel'].pop
    rejected { GiztestLayout.check_idle_gaps(doc, 'fixture') }
  end

  def test_late_suite_reconnects_before_first_registration
    doc = {'steps' => [rpc('a'), response('a', '4m'), rpc('b')]}
    rejected { GiztestLayout.check_idle_gaps(doc, 'fixture') }
    doc['steps'].insert(2, {'id' => 'b_reconnect', 'client' => 'b', 'reconnect' => {}})
    GiztestLayout.check_idle_gaps(doc, 'fixture')
  end

  def test_keepalive_must_be_registered_and_necessary
    status = rpc('a', 'run.status').merge('id' => 'a_setup_keepalive')
    doc = {'steps' => [rpc('a'), rpc('b'), response('b'), status, response('b')],
           'finally' => [rpc('a', 'run.stop')]}
    GiztestLayout.check_idle_gaps(doc, 'fixture')
    doc['steps'].delete_at(4)
    rejected { GiztestLayout.check_idle_gaps(doc, 'fixture') }
    doc['steps'] = [status]
    rejected { GiztestLayout.check_idle_gaps(doc, 'fixture') }
  end

  def test_cross_file_parity_rejects_input_gate_capture_and_cleanup_drift
    Dir.mktmpdir do |dir|
      left = File.join(dir, 'flowcraft.yaml'); right = File.join(dir, 'eino.yaml')
      source = {'variables' => {}, 'steps' => [audio_step.merge('id' => 'flowcraft_response', 'client' => 'flowcraft')],
                'finally' => [rpc('flowcraft', 'run.stop')]}
      File.write(left, YAML.dump(source))
      baseline = JSON.parse(JSON.generate(source).gsub('flowcraft', 'eino'))
      compare = lambda do |doc|
        File.write(right, YAML.dump(doc))
        GiztestLayout.compare_files(left, right, 'flowcraft', 'eino', {'flowcraft' => true, 'eino' => true})
      end
      compare.call(baseline)
      mutations = [
        ->(d) { d['steps'][0]['peer_stream']['input'] = 'different input' },
        ->(d) { d['steps'][0]['expect']['/first_text_ms']['maximum'] = 7000 },
        ->(d) { d['steps'][0]['capture'] = {'answer' => '/text'} },
        ->(d) { d['finally'] = [] }
      ]
      mutations.each do |mutate|
        changed = Marshal.load(Marshal.dump(baseline)); mutate.call(changed)
        rejected { compare.call(changed) }
      end
    end
  end

  def test_workspace_must_exist_before_selection
    create = {'id' => 'create', 'client' => 'doubao', 'rpc' => {
      'method' => 'server.workspace.create', 'request' => {'name' => '${workspace}'}}}
    select = {'id' => 'select', 'client' => 'doubao', 'rpc' => {
      'method' => 'server.run.workspace.set', 'request' => {'workspace_name' => '${workspace}'}}}
    GiztestLayout.check_workspace_order({'steps' => [create, select]}, 'fixture')
    rejected { GiztestLayout.check_workspace_order({'steps' => [select, create]}, 'fixture') }
  end

  def test_workspace_delete_requires_matching_local_creation
    create = {'id' => 'create', 'client' => 'a', 'rpc' => {
      'method' => 'server.workspace.create', 'request' => {'name' => '${workspace}'}}}
    delete = {'id' => 'delete', 'client' => 'a', 'rpc' => {
      'method' => 'server.workspace.delete', 'request' => {'name' => '${workspace}'}}}
    GiztestLayout.check_workspace_order({'steps' => [create], 'finally' => [delete]}, 'fixture')
    rejected { GiztestLayout.check_workspace_order({'steps' => [], 'finally' => [delete]}, 'fixture') }
    rejected { GiztestLayout.check_workspace_order({'steps' => [delete, create]}, 'fixture') }
    rejected { GiztestLayout.check_workspace_order({'steps' => [create], 'finally' => [delete.merge('client' => 'b')]}, 'fixture') }
    rejected { GiztestLayout.check_workspace_order({'steps' => [create], 'finally' => [delete, delete]}, 'fixture') }
  end

  def test_variant_ownership_does_not_overlap
    %w[flowcraft eino].each do |engine|
      multi = "#{engine}_multi_role"
      [engine, multi].each do |implementation|
        peer = {'id'=>"#{implementation}_response", 'client'=>"#{implementation}__transitions"}
        verdict = {'id'=>"#{implementation}_emit_verdict", 'output'=>{'variable'=>"#{implementation}_verdict"}}
        [peer, verdict].each do |step|
          assert GiztestLayout.owns?(step, implementation)
          refute GiztestLayout.owns?(step, implementation == engine ? multi : engine)
        end
      end
    end
  end

  def test_live_workflow_capabilities
    Dir['workflows/learn-*/raid.json'].each do |file|
      raid = File.basename(File.dirname(file))
      assert_equal({'flowcraft' => true, 'eino' => true}, GiztestLayout.tts_capabilities(raid))
    end
    assert_equal({'flowcraft' => true, 'eino_history' => true, 'eino_memory_async' => true,
                  'eino_memory_recall' => true}, GiztestLayout.tts_capabilities('journey-guide'))
  end

  def test_non_tts_rejects_every_audio_assertion_family
    GiztestLayout.check_audio(text_step, false, 'fixture')
    %w[audio_eos audio_eos_ms audio_bytes first_audio_ms audio_integrity/streams audio_pacing/underruns].each do |path|
      step = text_step
      step['expect']["/#{path}"] = {'equals' => 0}
      rejected { GiztestLayout.check_audio(step, false, 'fixture') }
    end
    step = text_step
    step['peer_stream']['first_audio_timeout'] = '3s'
    rejected { GiztestLayout.check_audio(step, false, 'fixture') }
    rejected { GiztestLayout.check_audio(audio_step, false, 'fixture') }
  end

  def test_tts_requires_audio_output_and_completion
    GiztestLayout.check_audio(audio_step, true, 'fixture')
    rejected { GiztestLayout.check_audio(text_step, true, 'fixture') }
    step = audio_step
    step['expect'].delete('/audio_eos')
    rejected { GiztestLayout.check_audio(step, true, 'fixture') }
    step['peer_stream']['completion'] = 'first_response'
    GiztestLayout.check_audio(step, true, 'fixture')
  end

  def test_projection_preserves_input_and_non_audio_assertions
    assert_equal GiztestLayout.without_audio([text_step]), GiztestLayout.without_audio([audio_step])
    ['input', '/text', '/first_text_ms'].each do |key|
      step = audio_step
      if key == 'input'
        step['peer_stream'][key] = '不同输入'
      else
        step['expect'][key] = {'maximum' => 1}
      end
      refute_equal GiztestLayout.without_audio([text_step]), GiztestLayout.without_audio([step])
    end
    refute_equal text_step, audio_step # Same-capability comparisons keep all audio fields.
  end
  def test_child_quality_rejects_exam_inputs_and_contract_drift
    doc = YAML.load_file('tests/giztest/quality/story-aesop.flowcraft.multi-role.giztest.yaml')
    GiztestLayout.check_child_quality(doc, 'fixture')
    changed = Marshal.load(Marshal.dump(doc))
    step = changed['steps'].find { |s| s['peer_stream'] }
    step['peer_stream']['input'] = '请只说这个角色知道的事。'
    rejected { GiztestLayout.check_child_quality(changed, 'fixture') }
    changed = Marshal.load(Marshal.dump(doc))
    step = changed['steps'].find { |s| s['peer_stream'] }
    step['expect']['/text']['min_length'] = 120
    rejected { GiztestLayout.check_child_quality(changed, 'fixture') }
  end

end
