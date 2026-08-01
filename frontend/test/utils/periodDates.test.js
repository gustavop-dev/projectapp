import { todayISO } from '../../utils/periodDates'

// The `process.env.TZ = 'America/Bogota'` technique (to reproduce the
// documented "toISOString() shifts to tomorrow after 19:00 in Bogotá" boundary
// directly) does NOT work in this repo's jest-environment-jsdom: the jsdom
// realm resolves Intl/Date to UTC at environment setup, before the test file
// runs, and mutating process.env.TZ afterwards has no effect on it (verified
// empirically: Intl.DateTimeFormat().resolvedOptions().timeZone stays 'UTC'
// even after setting process.env.TZ inside the test). Falling back to the
// call-count guard the brief names for this case: assert todayISO() never
// calls Date.prototype.toISOString(), which is exactly the operation that
// causes the documented off-by-one-day bug across a UTC-day boundary.
describe('todayISO', () => {
  afterEach(() => {
    jest.useRealTimers()
    jest.restoreAllMocks()
  })

  it('builds the date from local Date getters, never from toISOString', () => {
    jest.useFakeTimers()
    jest.setSystemTime(new Date('2026-08-01T15:30:00.000Z'))
    const toISOStringSpy = jest.spyOn(Date.prototype, 'toISOString')

    // Concrete expected value for the fixed system time above.
    expect(todayISO()).toBe('2026-08-01')
    // Fails if a future edit swaps the implementation back to
    // `d.toISOString().slice(0, 10)` — exactly the regression the file's own
    // comment (periodDates.js:1-2) warns about, which shifts the date by one
    // day whenever the local offset and UTC disagree about which calendar day
    // it is (e.g. after 19:00 in Bogotá, UTC-5).
    expect(toISOStringSpy).not.toHaveBeenCalled()
  })

  it('zero-pads single-digit month and day', () => {
    jest.useFakeTimers()
    jest.setSystemTime(new Date('2026-01-05T15:30:00.000Z'))

    // Fails if the pad(n) helper (periodDates.js:5) is dropped or broken,
    // producing '2026-1-5' instead of the zero-padded ISO shape callers rely on.
    expect(todayISO()).toBe('2026-01-05')
  })
})
