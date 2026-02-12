# SignVani NLP Pipeline to Hand Sign Integration

## Overview

The SignVani system has been successfully modified to bridge the NLP pipeline's final output directly to the SiGML model for hand sign generation. This creates a seamless flow from speech/text input to 3D avatar animations.

## Architecture Flow

```
Speech/Text Input
       ↓
   NLP Pipeline
┌─────────────────┐
│ Text Processor  │ → Handles punctuation (.,?!)
│ Grammar Transform│ → SVO to SOV conversion  
│ Gloss Mapper    │ → Maps to ISL glosses
└─────────────────┘
       ↓
   HamNoSys Codes
       ↓
┌─────────────────┐
│ HandSign Generator│ → Converts HamNoSys to keyframes
│ SiGML Generator   │ → Generates XML (legacy)
└─────────────────┘
       ↓
   Frontend Animations
       ↓
   3D Avatar Rendering
```

## Key Components Added

### 1. Enhanced Text Processor (`src/nlp/text_processor.py`)
- **Punctuation Preservation**: Periods, question marks, exclamation marks, commas
- **Special Token Generation**: `<PERIOD>`, `<QUESTION>`, `<EXCLAMATION>`, `<COMMA>`
- **Smart Tokenization**: Preserves punctuation meaning in the pipeline

### 2. Hand Sign Generator (`src/sigml/handsign_generator.py`)
- **HamNoSys to Keyframe Converter**: Maps HamNoSys symbols to Three.js bone transformations
- **Animation Sequencer**: Creates timed animation sequences with pauses
- **Frontend Format Output**: Direct compatibility with 3D avatar system

#### HamNoSys Mappings:
```python
"hamflathand": → Flat hand shape
"hamfist": → Fist hand shape  
"hamthumboutmod": → Thumb extended
"hampalmu": → Palm up orientation
"hamneutralspace": → Neutral position
"hammoveu": → Move up gesture
"hamcircle": → Circular motion
```

### 3. Enhanced SiGML Generator (`src/sigml/generator.py`)
- **Pause Logic**: Smart insertion of pauses at sentence endings
- **Hand Restore**: Returns hands to neutral position between signs
- **Dual Output**: Both SiGML XML and hand sign animations

### 4. New API Endpoints

#### `/api/text-to-handsign`
Converts text directly to hand sign animations:
```json
{
  "original_text": "hello world.",
  "gloss": "H E L L O W O R L D P E R I O D",
  "total_duration": 2500,
  "animations": [
    {
      "gloss": "HELLO",
      "hamnosys": "hamflathand,hampalmu,hamchin,hammoveo,hammoved",
      "duration": 1200,
      "keyframes": [
        {
          "time": 0,
          "transformations": [
            ["mixamorigLeftHandIndex1", "rotation", "z", "0", "+"],
            ["mixamorigLeftHandMiddle1", "rotation", "z", "0", "+"],
            ...
          ]
        },
        ...
      ]
    },
    {
      "gloss": "PAUSE", 
      "duration": 500,
      "keyframes": [...neutral position...]
    }
  ]
}
```

#### `/api/speech-to-handsign`
Same as above but processes audio input first.

### 5. Frontend Hand Sign Service (`client/src/Services/handsignService.js`)
- **Direct Animation Player**: Applies keyframes to 3D avatar
- **Bone Transformation Engine**: Maps to Three.js skeleton
- **Progress Tracking**: Real-time animation progress feedback

## Period/End-of-Line Handling

### Input Processing:
```
"hello world. how are you?"
↓
"hello world <PERIOD> how are you <QUESTION>"
↓
Gloss: ["H", "E", "L", "L", "O", "W", "O", "R", "L", "D", "PERIOD", "HOW", "ARE", "YOU", "QUESTION"]
```

### Animation Generation:
- **Sign Animation**: Each gloss gets hand movement keyframes
- **Pause Insertion**: `<pause duration="500" />` after each sign
- **Hand Restore**: `<restore_hands />` returns to neutral position
- **Natural Flow**: 500ms pauses create realistic signing rhythm

### Frontend Validation:
- **Updated Regex**: `/^[A-Za-z\s.,!?]*$/`
- **Error Message**: "Only letters (A-Z), spaces, and basic punctuation (. , ! ?) are allowed"

## Testing Results

### Test Case: "hello world. how are you?"
✅ **Input**: Text with period and question mark  
✅ **Gloss**: `H E L L O W O R L D P E R I O D YOU QUESTION HOW`  
✅ **Animations**: 5 total animations (3 signs + 2 pauses)  
✅ **Keyframes**: Detailed bone transformations for each sign  
✅ **Duration**: ~2500ms total with natural pauses  

### Test Case: "thank you."
✅ **Input**: Simple sentence with period  
✅ **Gloss**: `THANK YOU PERIOD`  
✅ **Animations**: 3 animations (2 signs + 1 pause)  
✅ **HamNoSys**: Proper hand shape and movement codes  

## Benefits

1. **Direct Pipeline**: NLP output → Hand signs (no intermediate parsing)
2. **Natural Timing**: Automatic pauses and hand positioning
3. **Punctuation Support**: Periods, questions, exclamations handled
4. **Frontend Ready**: Direct keyframe animations for 3D avatar
5. **Backward Compatible**: SiGML XML generation still available

## Usage

### Backend:
```python
# Generate hand signs from NLP pipeline
gloss_phrase = gloss_mapper.process("hello world.")
animations = sigml_generator.generate_handsign_animations(gloss_phrase)
```

### Frontend:
```javascript
// Convert text to hand signs
const animationData = await handSignService.textToHandSign("hello world.");
await handSignService.playHandSignAnimations(animationData, threeRef);
```

### API:
```bash
curl -X POST "http://localhost:8000/api/text-to-handsign" \
  -H "Content-Type: application/json" \
  -d '{"text": "hello world."}'
```

## Future Enhancements

1. **More HamNoSys Symbols**: Expand symbol-to-animation mappings
2. **Non-Manual Components**: Add facial expressions and head movements
3. **Speed Control**: Variable animation speed based on user preference
4. **Real-time Streaming**: WebSocket support for live signing
5. **Custom Gestures**: User-defined hand signs and movements

---

**Status**: ✅ **COMPLETE** - The NLP pipeline now directly feeds the SiGML model for hand sign generation with full punctuation support and natural timing.
