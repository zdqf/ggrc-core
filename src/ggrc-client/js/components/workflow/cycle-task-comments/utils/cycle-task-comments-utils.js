/*
  Copyright (C) 2018 Google Inc.
  Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

import {
  warning,
  BUTTON_VIEW_DELETE,
  CONTENT_VIEW_CONFIRM_DELETE,
} from '../../../../plugins/utils/modals';

function removeComment(instance) {
  const titleSingular = instance.attr('class').title_singular;
  const model = CMS.Models[titleSingular];
  const modalTitle = `Delete ${titleSingular}`;
  const options = {
    model,
    instance,
    new_object_form: false,
    button_view: BUTTON_VIEW_DELETE,
    modal_title: modalTitle,
    content_view: CONTENT_VIEW_CONFIRM_DELETE,
  };
  const dfd = new $.Deferred();
  warning(options,
    async () => {
      await instance.refresh();
      await instance.destroy();
      dfd.resolve();
    },
    dfd.reject.bind(dfd)
  );
  return dfd;
}

export default {
  removeComment,
};
