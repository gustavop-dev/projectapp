import { downloadBlob, filenameFromDisposition } from '../../utils/downloadFile';

describe('downloadBlob', () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('downloads through a temporary revoked object-url anchor', () => {
    URL.createObjectURL = jest.fn().mockReturnValue('blob:fake-url');
    URL.revokeObjectURL = jest.fn();
    const click = jest
      .spyOn(HTMLAnchorElement.prototype, 'click')
      .mockImplementation(() => {});

    downloadBlob(new Blob(['pdf']), 'reporte.pdf');

    expect(URL.createObjectURL).toHaveBeenCalledTimes(1);
    expect(click).toHaveBeenCalledTimes(1);
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:fake-url');
    expect(document.querySelector('a[download]')).toBeNull();
  });
});

describe('filenameFromDisposition', () => {
  it('extracts a quoted filename', () => {
    expect(filenameFromDisposition('attachment; filename="Extracto_Junio.pdf"'))
      .toBe('Extracto_Junio.pdf');
  });

  it('extracts an unquoted filename', () => {
    expect(filenameFromDisposition('attachment; filename=reporte.xlsx'))
      .toBe('reporte.xlsx');
  });

  it('returns empty for a missing header', () => {
    expect(filenameFromDisposition('')).toBe('');
  });
});
