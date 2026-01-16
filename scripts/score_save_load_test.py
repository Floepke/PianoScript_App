import os
import sys
import pprint

# Ensure workspace root is on sys.path when running from scripts/
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from file_model.SCORE import SCORE

def main():
    # Create a fresh SCORE, add a couple of events
    score = SCORE().new()
    score.new_note(pitch=48, time=0.0, duration=120.0, hand='<')
    score.new_line_break(time=0.0, margin_mm=[10.0, 10.0], stave_range=[0, 0])

    out_path = os.path.join('/tmp', 'score_save_load_test.piano')
    
    # Save to tmp
    score.save(out_path)

    # Load back
    loaded = SCORE().load(out_path)

    # save again
    loaded.save(out_path)

    # Print the loaded class/instance for verification
    print('Loaded SCORE type:', type(loaded))
    pprint.pprint(loaded)

if __name__ == '__main__':
    main()
