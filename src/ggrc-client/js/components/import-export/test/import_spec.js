/*
  Copyright (C) 2018 Google Inc.
  Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

import Component from '../import';
import {getComponentVM} from '../../../../js_specs/spec_helpers';
import * as ieUtils from '../import-export-utils';
import {
  jobStatuses,
} from '../import-export-utils';
import {backendGdriveClient} from '../../../plugins/ggrc-gapi-client';

describe('csv-import component', () => {
  let vm;
  beforeEach(() => {
    vm = getComponentVM(Component);
  });

  describe('isDownloadTemplateAvailable getter', () => {
    it('should be true for analysis state', () => {
      vm.attr('state', jobStatuses.ANALYSIS);
      expect(vm.attr('isDownloadTemplateAvailable')).toEqual(false);
    });

    it('should be true for in progress state', () => {
      vm.attr('state', jobStatuses.IN_PROGRESS);
      expect(vm.attr('isDownloadTemplateAvailable')).toEqual(false);
    });

    it('should be false for default state of component', () => {
      expect(vm.attr('isDownloadTemplateAvailable')).toEqual(true);
    });

    it('should be true for "analysis failed" state', () => {
      vm.attr('state', jobStatuses.ANALYSIS_FAILED);
      expect(vm.attr('isDownloadTemplateAvailable')).toEqual(true);
    });

    it('should be true for "stopped" state', () => {
      vm.attr('state', jobStatuses.STOPPED);
      expect(vm.attr('isDownloadTemplateAvailable')).toEqual(true);
    });

    it('should be true for "failed" state', () => {
      vm.attr('state', jobStatuses.FAILED);
      expect(vm.attr('isDownloadTemplateAvailable')).toEqual(true);
    });
  });

  describe('resetFile() method', () => {
    it('should reset file\'s info', () => {
      vm.attr({
        state: jobStatuses.IN_PROGRESS,
        fileId: 'Foo',
        fileName: 'Bar.csv',
        importStatus: 'error',
        message: 'Warning!',
      });
      vm.resetFile();
      expect(vm.attr('state')).toEqual(jobStatuses.SELECT);
      expect(vm.attr('fileId')).toEqual('');
      expect(vm.attr('fileName')).toEqual('');
      expect(vm.attr('importStatus')).toEqual('');
      expect(vm.attr('message')).toEqual('');
    });
  });

  describe('analyseSelectedFile() method', () => {
    it('should reset state to "Select" for empty files', (done) => {
      spyOn(backendGdriveClient, 'withAuth')
        .and.returnValue(can.Deferred().resolve({
          objects: {
            Foo: 0,
            Bar: 0,
            Baz: 0,
          },
        }));

      vm.analyseSelectedFile({
        id: 42,
        name: 'file.csv',
      }).then(() => {
        expect(vm.attr('fileId')).toEqual(42);
        expect(vm.attr('fileName')).toEqual('file.csv');
        expect(vm.attr('state')).toEqual(jobStatuses.SELECT);
        expect(vm.attr('importStatus')).toEqual('error');
        expect(vm.attr('message')).toBeTruthy();

        done();
      });
    });

    it('should reset state to "Select" after error on GDrive side', (done) => {
      spyOn(backendGdriveClient, 'withAuth')
        .and.returnValue(can.Deferred().reject({
          responseJSON: {
            message: 'GDrive error message',
          },
        }));

      spyOn(GGRC.Errors, 'notifier');

      vm.analyseSelectedFile({
        id: 42,
        name: 'file.csv',
      }).fail(() => {
        expect(vm.attr('fileId')).toEqual(42);
        expect(vm.attr('fileName')).toEqual('file.csv');
        expect(vm.attr('state')).toEqual(jobStatuses.SELECT);
        expect(vm.attr('importStatus')).toEqual('error');
        expect(GGRC.Errors.notifier)
          .toHaveBeenCalledWith('error', 'GDrive error message');

        done();
      });
    });

    it('should set the correct status about import job', (done) => {
      spyOn(backendGdriveClient, 'withAuth')
        .and.returnValue(can.Deferred().resolve({
          objects: {
            Foo: 15,
            Bar: 5,
            Baz: 19,
          },
          import_export: {
            id: 13,
            status: 'New Status',
          },
        }));

      vm.analyseSelectedFile({
        id: 42,
        name: 'file.csv',
      }).then(() => {
        expect(vm.attr('fileId')).toEqual(42);
        expect(vm.attr('fileName')).toEqual('file.csv');
        expect(vm.attr('state')).toEqual('New Status');
        expect(vm.attr('jobId')).toEqual(13);

        expect(vm.attr('message')).toBeTruthy();

        done();
      });
    });
  });

  describe('startImport() method', () => {
    beforeEach(() => {
      spyOn(ieUtils, 'startImport')
        .and.returnValue(can.Deferred().resolve({id: 1}));

      spyOn(vm, 'trackStatusOfImport');
    });

    it('should set correct status and launch the tracking of job', (done) => {
      vm.attr('jobId', 10);

      vm.startImport('State')
        .then(() => {
          expect(vm.attr('state')).toEqual('State');
          expect(vm.attr('message')).toBeTruthy();

          expect(ieUtils.startImport).toHaveBeenCalledWith(10);
          expect(vm.trackStatusOfImport).toHaveBeenCalledWith(1);

          done();
        });
    });
  });

  describe('trackStatusOfImport() method', () => {
    const statuses = Object.values(jobStatuses);

    beforeEach(() => {
      statuses.forEach((state) => {
        spyOn(vm.attr('statusStrategies'), state);
      });
    });

    describe('should call correct status strategy', () => {
      statuses.forEach((status) => {
        it(`for the ${status} status`, (done) => {
          spyOn(ieUtils, 'getImportJobInfo')
            .and.returnValue(can.Deferred().resolve({status}));

          vm.trackStatusOfImport(1, 0);

          setTimeout(() => {
            expect(ieUtils.getImportJobInfo).toHaveBeenCalledWith(1);
            expect(vm.attr('statusStrategies')[status]).toHaveBeenCalled();

            expect(vm.attr('state')).toEqual(status);
            done();
          }, 10);
        });
      });
    });
  });

  describe('getImportHistory() method', () => {
    beforeEach(() => {
      spyOn(vm, 'trackStatusOfImport');
    });

    describe('with empty history', () => {
      beforeEach(() => {
        spyOn(ieUtils, 'getImportHistory')
          .and.returnValue(can.Deferred().resolve([]));

        spyOn(ieUtils, 'isInProgressJob');
      });

      it('should not define a history list', (done) => {
        vm.getImportHistory()
          .then(() => {
            expect(ieUtils.isInProgressJob).not.toHaveBeenCalled();
            expect(vm.trackStatusOfImport).not.toHaveBeenCalled();

            expect(vm.attr('history').length).toEqual(0);
            done();
          });
      });
    });

    describe('with existing jobs in the history', () => {
      describe('and last job with "In Progress" state', () => {
        beforeEach(() => {
          spyOn(ieUtils, 'getImportHistory')
            .and.returnValue(can.Deferred().resolve([
              {
                id: 1,
                status: jobStatuses.FINISHED,
                title: 'import_1.csv',
              }, {
                id: 2,
                status: jobStatuses.FINISHED,
                title: 'import_2.csv',
              }, {
                id: 3,
                status: jobStatuses.FAILED,
                title: 'import_3.csv',
              }, {
                id: 4,
                status: jobStatuses.FINISHED,
                title: 'import_4.csv',
              }, {
                id: 5,
                status: jobStatuses.IN_PROGRESS,
                title: 'import_5.csv',
              },
            ]));
        });

        it('should define correct history and state of "In Progress job"',
          (done) => {
            vm.getImportHistory()
              .then(() => {
                expect(vm.trackStatusOfImport).toHaveBeenCalled();

                expect(vm.attr('history').length).toEqual(3);
                expect(vm.attr('history')[0].id).toEqual(4);
                expect(vm.attr('history')[1].id).toEqual(2);
                expect(vm.attr('history')[2].id).toEqual(1);
                done();
              });
          });
      });

      describe('and last job is completed', () => {
        beforeEach(() => {
          spyOn(ieUtils, 'getImportHistory')
            .and.returnValue(can.Deferred().resolve([
              {
                id: 1,
                status: jobStatuses.FAILED,
                title: 'import_1.csv',
              }, {
                id: 2,
                status: jobStatuses.FINISHED,
                title: 'import_2.csv',
              }, {
                id: 3,
                status: jobStatuses.FAILED,
                title: 'import_3.csv',
              }, {
                id: 4,
                status: jobStatuses.FINISHED,
                title: 'import_4.csv',
              }, {
                id: 5,
                status: jobStatuses.FINISHED,
                title: 'import_5.csv',
              },
            ]));
        });

        it('should not define file state', (done) => {
          vm.getImportHistory()
            .then(() => {
              expect(vm.trackStatusOfImport).not.toHaveBeenCalled();

              expect(vm.attr('history').length).toEqual(3);
              expect(vm.attr('history')[0].id).toEqual(5);
              expect(vm.attr('history')[1].id).toEqual(4);
              expect(vm.attr('history')[2].id).toEqual(2);
              done();
            });
        });
      });
    });
  });
});
