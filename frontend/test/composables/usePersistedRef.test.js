import { usePersistedRef } from '../../composables/usePersistedRef';

beforeEach(() => {
  localStorage.clear();
});

describe('usePersistedRef', () => {
  describe('read', () => {
    it('returns null when key is missing', () => {
      const { read } = usePersistedRef('missing-key');
      expect(read()).toBeNull();
    });

    it('returns deserialized stored value', () => {
      localStorage.setItem('present-key', 'true');
      const { read } = usePersistedRef('present-key');
      expect(read()).toBe(true);
    });

    it('returns null when deserialize throws on invalid JSON', () => {
      localStorage.setItem('bad-json', 'not-json');
      const { read } = usePersistedRef('bad-json');
      expect(read()).toBeNull();
    });

    it('returns null when localStorage.getItem throws', () => {
      localStorage.setItem('any-key', 'true');
      const original = Storage.prototype.getItem;
      Storage.prototype.getItem = jest.fn(() => { throw new Error('access'); });
      const { read } = usePersistedRef('any-key');
      expect(read()).toBeNull();
      Storage.prototype.getItem = original;
    });

    it('uses custom deserialize when provided', () => {
      localStorage.setItem('theme', 'dark');
      const { read } = usePersistedRef('theme', null, {
        deserialize: (s) => (s === 'dark' ? true : false),
      });
      expect(read()).toBe(true);
    });
  });

  describe('write', () => {
    it('serializes value with JSON by default', () => {
      const { write } = usePersistedRef('write-key');
      write({ a: 1 });
      expect(localStorage.getItem('write-key')).toBe('{"a":1}');
    });

    it('uses custom serialize when provided', () => {
      const { write } = usePersistedRef('theme', null, {
        serialize: (v) => (v ? 'dark' : 'light'),
      });
      write(true);
      expect(localStorage.getItem('theme')).toBe('dark');
    });

    it('does not throw when localStorage.setItem fails', () => {
      const { write } = usePersistedRef('quota');
      const original = Storage.prototype.setItem;
      Storage.prototype.setItem = jest.fn(() => { throw new Error('quota'); });
      expect(() => write(true)).not.toThrow();
      Storage.prototype.setItem = original;
    });
  });

  describe('remove', () => {
    it('deletes the key from localStorage', () => {
      localStorage.setItem('to-remove', 'true');
      const { remove } = usePersistedRef('to-remove');
      remove();
      expect(localStorage.getItem('to-remove')).toBeNull();
    });
  });

  describe('ref', () => {
    it('initializes to defaultValue when storage is empty', () => {
      const { ref: r } = usePersistedRef('empty', false);
      expect(r.value).toBe(false);
    });

    it('initializes to stored value when present', () => {
      localStorage.setItem('preset', 'true');
      const { ref: r } = usePersistedRef('preset', false);
      expect(r.value).toBe(true);
    });
  });
});
