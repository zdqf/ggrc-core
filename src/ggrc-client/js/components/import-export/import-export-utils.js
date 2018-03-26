/*
  Copyright (C) 2018 Google Inc.
  Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

const currentUserId = GGRC.current_user.id;

export const jobStatuses = {
  SELECT: 'Select',
  NOT_STARTED: 'Not Started',
  ANALYSIS: 'Analysis',
  IN_PROGRESS: 'In Progress',
  BLOCKED: 'Blocked',
  ANALYSIS_FAILED: 'Analysis Failed',
  STOPPED: 'Stopped',
  FAILED: 'Failed',
  FINISHED: 'Finished',
};

export const isStoppedJob = (jobStatus) => {
  return [jobStatuses.BLOCKED, jobStatuses.ANALYSIS_FAILED].includes(jobStatus);
};

export const isInProgressJob = (jobStatus) => {
  return [
    jobStatuses.NOT_STARTED,
    jobStatuses.ANALYSIS,
    jobStatuses.IN_PROGRESS,
    jobStatuses.BLOCKED,
    jobStatuses.ANALYSIS_FAILED,
  ].includes(jobStatus);
};

export const runExport = (options) => {
  return request(`/api/people/${currentUserId}/exports`, 'POST', options);
};

export const getExportJob = (jobId) => {
  return request(`/api/people/${currentUserId}/exports/${jobId}`, 'GET');
};

export const getExportsHistory = (ids) => {
  let data;

  if (ids) {
    data = {
      id__in: ids.join(', '),
    };
  }
  return request(`/api/people/${currentUserId}/exports`, 'GET', data);
};

export const stopExportJob = (jobId) => {
  return request(`/api/people/${currentUserId}/exports/${jobId}/stop`, 'PUT');
};

export const deleteExportJob = (jobId) => {
  return request(`/api/people/${currentUserId}/exports/${jobId}`, 'DELETE');
};

export const exportRequest = (request) => {
  return $.ajax({
    type: 'POST',
    headers: $.extend({
      'Content-Type': 'application/json',
      'X-export-view': 'blocks',
      'X-requested-by': 'GGRC',
    }, request.headers || {}),
    url: '/_service/export_csv',
    data: JSON.stringify(request.data || {}),
  });
};

export const analyseBeforeImport = (fileId) => {
  return request(`/api/people/${currentUserId}/imports`, 'POST', {id: fileId});
};

export const startImport = (jobId) => {
  return request(`/api/people/${currentUserId}/imports/${jobId}/start`, 'PUT');
};

export const stopImportJob = (jobId) => {
  return request(`/api/people/${currentUserId}/imports/${jobId}/stop`, 'PUT');
};

export const getImportJobInfo = (jobId) => {
  return request(`/api/people/${currentUserId}/imports/${jobId}`, 'GET');
};

export const getImportHistory = () => {
  return request(`/api/people/${currentUserId}/imports`, 'GET');
};

export const deleteImportJob = (jobId) => {
  return request(`/api/people/${currentUserId}/imports/${jobId}`, 'DELETE');
};

export const downloadContent = (jobId, format = 'csv') => {
  return request(`/api/people/${currentUserId}/imports/${jobId}/download`,
    'GET', {
      export_to: format,
    });
};

export const downloadExportContent = (jobId, format = 'csv') => {
  return request(`/api/people/${currentUserId}/exports/${jobId}/download`,
    'GET', {
      export_to: format,
    });
};

export const download = (filename, text) => {
  let TMP_FILENAME = filename || 'export_objects.csv';

  // a helper for opening the "Save File" dialog to save downloaded data
  function promptSaveFile() {
    let downloadURL = [
      'filesystem:', window.location.origin, '/temporary/', TMP_FILENAME,
    ].join('');

    let link = document.createElement('a');

    link.setAttribute('href', downloadURL);
    link.setAttribute('download', TMP_FILENAME);
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  function errorHandler(error) {
    console.error('LocalFileSys error:', error);
  }

  // a callback for when the browser's virtual file system is obtained
  function fileSystemObtained(localstorage) {
    localstorage.root.getFile(
      TMP_FILENAME, {create: true}, fileEntryObtained, errorHandler);
  }

  // a helper that writes thee downloaded data to a tmeporary file
  // and then opens the "Save File" dialog
  function fileEntryObtained(fileEntry) {
    fileEntry.createWriter(function (fileWriter) {
      let truncated = false;

      // the onwriteevent fires twice - once after truncating the file,
      // and then after writing the downloaded text content to it
      fileWriter.onwriteend = function (ev) {
        let blob;
        if (!truncated) {
          truncated = true;
          blob = new Blob([text], {type: 'text/plain'});
          fileWriter.write(blob);
        } else {
          promptSaveFile();
        }
      };

      fileWriter.onerror = function (ev) {
        console.error('Writing temp file failed: ' + ev.toString());
      };

      fileWriter.truncate(0); // in case the file exists and is non-empty
    }, errorHandler);
  }

  // start storing the downloaded data to a temporary file for the user to
  // save it on his/her computers storage
  window.webkitRequestFileSystem(
    window.TEMPORARY, text.length, fileSystemObtained, errorHandler);
};

export const fileSafeCurrentDate = () => {
  return moment().format('YYYY-MM-DD_HH-mm-ss');
};

const request = (url, type = 'POST', data) => {
  const params = {
    url,
    type,
    headers: {
      'Content-Type': 'application/json',
      'X-requested-by': 'GGRC',
    },
  };

  if (data) {
    params.data = data;
  }

  return $.ajax(params);
};
