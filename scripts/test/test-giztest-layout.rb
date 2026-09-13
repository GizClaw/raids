require 'minitest/autorun'
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

  def test_live_workflow_capabilities
    Dir['workflows/learn-*/raid.json'].each do |file|
      raid = File.basename(File.dirname(file))
      assert_equal({'flowcraft' => true, 'eino' => false}, GiztestLayout.tts_capabilities(raid))
    end
    assert_equal({'flowcraft' => true, 'eino_history' => false, 'eino_memory_async' => false,
                  'eino_memory_recall' => false}, GiztestLayout.tts_capabilities('journey-guide'))
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
end
