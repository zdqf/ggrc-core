/*
  Copyright (C) 2018 Google Inc.
  Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

import * as importExportUtils from '../import-export-utils';

const baseUrlPrefix = '/api/people/1';

const ajaxSpy = () => {
  return spyOn($, 'ajax');
};

const calledWithOptions = (url, type = 'POST', data) => {
  const options = Object.assign({
    headers: {
      'Content-Type': 'application/json',
      'X-requested-by': 'GGRC',
    },
  }, {url, type});

  if (data) {
    options.data = data;
  }
  expect($.ajax).toHaveBeenCalledWith(options);
};

describe('Import/Export utils', () => {
  describe('isStoppedJob() method', () => {
    it('should return true for "Blocked" job', () => {
      expect(importExportUtils.isStoppedJob('Blocked')).toEqual(true);
    });

    it('should return true for "Analysis Failed" job', () => {
      expect(importExportUtils.isStoppedJob('Analysis Failed')).toEqual(true);
    });

    it('should return false for not defined status of job', () => {
      expect(importExportUtils.isStoppedJob()).toEqual(false);
    });

    it('should return false for "Select" job', () => {
      expect(importExportUtils.isStoppedJob('Select')).toEqual(false);
    });

    it('should return false for "Not Started" job', () => {
      expect(importExportUtils.isStoppedJob('Not Started')).toEqual(false);
    });

    it('should return false for "Analysis" job', () => {
      expect(importExportUtils.isStoppedJob('Analysis')).toEqual(false);
    });

    it('should return false for "In Progress" job', () => {
      expect(importExportUtils.isStoppedJob('In Progress')).toEqual(false);
    });

    it('should return false for "Stopped" job', () => {
      expect(importExportUtils.isStoppedJob('Stopped')).toEqual(false);
    });

    it('should return false for "Failed" job', () => {
      expect(importExportUtils.isStoppedJob('Failed')).toEqual(false);
    });

    it('should return false for "Finished" job', () => {
      expect(importExportUtils.isStoppedJob('Finished')).toEqual(false);
    });
  });

  describe('isInProgressJob() method', () => {
    it('should return false for "Not Started" job', () => {
      expect(importExportUtils.isInProgressJob('Not Started')).toEqual(true);
    });

    it('should return false for "Analysis" job', () => {
      expect(importExportUtils.isInProgressJob('Analysis')).toEqual(true);
    });

    it('should return false for "In Progress" job', () => {
      expect(importExportUtils.isInProgressJob('In Progress')).toEqual(true);
    });

    it('should return true for "Blocked" job', () => {
      expect(importExportUtils.isInProgressJob('Blocked')).toEqual(true);
    });

    it('should return true for "Analysis Failed" job', () => {
      expect(importExportUtils.isInProgressJob('Blocked')).toEqual(true);
    });

    it('should return false for not defined status of job', () => {
      expect(importExportUtils.isInProgressJob()).toEqual(false);
    });

    it('should return false for "Select" job', () => {
      expect(importExportUtils.isInProgressJob('Select')).toEqual(false);
    });

    it('should return false for "Stopped" job', () => {
      expect(importExportUtils.isInProgressJob('Stopped')).toEqual(false);
    });

    it('should return false for "Failed" job', () => {
      expect(importExportUtils.isInProgressJob('Failed')).toEqual(false);
    });

    it('should return false for "Finished" job', () => {
      expect(importExportUtils.isInProgressJob('Finished')).toEqual(false);
    });
  });

  describe('runExport() method', () => {
    it('should call correct endpoint', () => {
      ajaxSpy();
      importExportUtils.runExport('FooBar');
      calledWithOptions(`${baseUrlPrefix}/exports`, 'POST', 'FooBar');
    });
  });

  describe('getExportJob() method', () => {
    it('should call correct endpoint', () => {
      ajaxSpy();
      importExportUtils.getExportJob(13);
      calledWithOptions(`${baseUrlPrefix}/exports/13`, 'GET');
    });
  });

  describe('getExportsHistory() method', () => {
    it('should call correct endpoint', () => {
      ajaxSpy();
      importExportUtils.getExportsHistory();
      calledWithOptions(`${baseUrlPrefix}/exports`, 'GET');
    });
  });

  describe('stopExportJob() method', () => {
    it('should call correct endpoint', () => {
      ajaxSpy();
      importExportUtils.stopExportJob(2);
      calledWithOptions(`${baseUrlPrefix}/exports/2/stop`, 'PUT');
    });
  });

  describe('deleteExportJob() method', () => {
    it('should call correct endpoint', () => {
      ajaxSpy();
      importExportUtils.deleteExportJob(13);
      calledWithOptions(`${baseUrlPrefix}/exports/13`, 'DELETE');
    });
  });

  describe('analyseBeforeImport() method', () => {
    it('should call correct endpoint', () => {
      ajaxSpy();
      importExportUtils.analyseBeforeImport(12);
      calledWithOptions(`${baseUrlPrefix}/imports`, 'POST', {id: 12});
    });
  });

  describe('startImport() method', () => {
    it('should call correct endpoint', () => {
      ajaxSpy();
      importExportUtils.startImport(10);
      calledWithOptions(`${baseUrlPrefix}/imports/10/start`, 'PUT');
    });
  });

  describe('getImportJobInfo() method', () => {
    it('should call correct endpoint', () => {
      ajaxSpy();
      importExportUtils.getImportJobInfo(10);
      calledWithOptions(`${baseUrlPrefix}/imports/10`, 'GET');
    });
  });

  describe('getImportHistory() method', () => {
    it('should call correct endpoint', () => {
      ajaxSpy();
      importExportUtils.getImportHistory();
      calledWithOptions(`${baseUrlPrefix}/imports`, 'GET');
    });
  });

  describe('deleteImportJob() method', () => {
    it('should call correct endpoint', () => {
      ajaxSpy();
      importExportUtils.deleteImportJob(10);
      calledWithOptions(`${baseUrlPrefix}/imports/10`, 'DELETE');
    });
  });

  describe('downloadContent() method', () => {
    it('should call correct endpoint and csv format', () => {
      ajaxSpy();
      importExportUtils.downloadContent(10);
      calledWithOptions(`${baseUrlPrefix}/imports/10/download`, 'GET', {
        export_to: 'csv',
      });
    });

    it('should call correct endpoint and gdrive format', () => {
      ajaxSpy();
      importExportUtils.downloadContent(10, 'gdrive');
      calledWithOptions(`${baseUrlPrefix}/imports/10/download`, 'GET', {
        export_to: 'gdrive',
      });
    });
  });

  describe('downloadExportContent() method', () => {
    it('should call correct endpoint for csv format', () => {
      ajaxSpy();
      importExportUtils.downloadExportContent(10);
      calledWithOptions(`${baseUrlPrefix}/exports/10/download`, 'GET', {
        export_to: 'csv',
      });
    });

    it('should call correct endpoint for gdrive format', () => {
      ajaxSpy();
      importExportUtils.downloadExportContent(10, 'gdrive');
      calledWithOptions(`${baseUrlPrefix}/exports/10/download`, 'GET', {
        export_to: 'gdrive',
      });
    });
  });
});
