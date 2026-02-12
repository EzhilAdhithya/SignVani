// JSON-based word loading system
// All word animations are now loaded from wordsData.json
import { loadAllWords, getAvailableWordsFromJSON } from './Utils/wordLoader';

// Load all words from JSON
const loadedWords = loadAllWords();

// Export individual word animation functions (for backward compatibility)
export const TIME = loadedWords.TIME;
export const HOME = loadedWords.HOME;
export const PERSON = loadedWords.PERSON;
export const YOU = loadedWords.YOU;
export const HELLO = loadedWords.HELLO;
export const THANK = loadedWords.THANK;
export const PLEASE = loadedWords.PLEASE;
export const SORRY = loadedWords.SORRY;
export const YES = loadedWords.YES;
export const NO = loadedWords.NO;
export const HELP = loadedWords.HELP;
export const NAME = loadedWords.NAME;
export const FAMILY = loadedWords.FAMILY;
export const FRIEND = loadedWords.FRIEND;
export const WORK = loadedWords.WORK;
export const SCHOOL = loadedWords.SCHOOL;
export const EAT = loadedWords.EAT;
export const DRINK = loadedWords.DRINK;
export const GOOD = loadedWords.GOOD;
export const BAD = loadedWords.BAD;

// Export wordList (automatically generated from JSON)
export const wordList = getAvailableWordsFromJSON();