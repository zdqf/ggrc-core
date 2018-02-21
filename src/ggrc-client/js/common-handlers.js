/*
    Copyright (C) 2018 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

import Spinner from 'spin.js';

var $body = $('body');
var $window = $(window);

// We remove loading class
$window.on('load', function () {
  $('html').removeClass('no-js');
});

$body.on("click", ".lhn-no-init", function() {
  $(this).removeClass('lhn-no-init');
  import(/* webpackChunkName: "lhn" */'./controllers/lhn_controllers')
    .then(function () {
      $("#lhn").cms_controllers_lhn();
      $(document.body).ggrc_controllers_recently_viewed();
    });
});

$body.on("click", "a[data-toggle=unmap]", function(ev) {
  var $el = $(this)
  ;
  //  Prevent toggling `openclose` state in trees
  ev.stopPropagation();
  $el.fadeTo('fast', 0.25);
  $el.children(".result").each(function(i, result_el) {
    var $result_el = $(result_el)
      , result = $result_el.data('result')
      , mappings = result && result.get_mappings()
      , i
    ;

    function notify(instance){
      $(document.body).trigger(
        "ajax:flash"
        , {"success" : "Unmap successful."}
      );
    }

    can.each(mappings, function(mapping) {
      mapping.refresh().done(function() {
        if (mapping instanceof CMS.Models.Control) {
          mapping.removeAttr('directive');
          mapping.save().then(notify);
        }
        else {
          mapping.destroy().then(notify);
        }
      });
    });
  });
});

// Initialize delegated event handlers
jQuery(function ($) {
  window.natural_comparator = function (a, b) {
    var i;
    a = a.slug.toString();
    b = b.slug.toString();
    if (a === b) {
      return 0;
    }

    a = a.replace(/(?=\D\d)(.)|(?=\d\D)(.)/g, '$1$2|').split('|');
    b = b.replace(/(?=\D\d)(.)|(?=\d\D)(.)/g, '$1$2|').split('|');

    for (i = 0; i < Math.max(a.length, b.length); i++) {
      if (Number(a[i]) === Number(a[i]) && Number(b[i]) === Number(b[i])) {
        if (Number(a[i]) < Number(b[i])) {
          return -1;
        }
        if (Number(b[i]) < Number(a[i])) {
          return 1;
        }
      } else {
        if (a[i] < b[i]) {
          return -1;
        }
        if (b[i] < a[i]) {
          return 1;
        }
      }
    }
    return 0;
  };

  // Turn the arrow when tree node content is shown
  $body.on('click', '[data-toggle="collapse"]', function (e) {
    var $this = $(this);
    var $expander_container = $this.closest(':has(.expander, .enddot)');
    var $expander = $expander_container.find('.expander').eq(0);
    var $target = $($this.data('target'));

    setTimeout(function () {
      if ($target.hasClass('in')) {
        $expander.addClass('in');
      } else {
        $expander.removeClass('in');
      }
    }, 100);
  });

  // After the modal template has loaded from the server, but before the
  //  data has loaded to populate into the body, show a spinner
  $body.on('loaded', '.modal.modal-slim, .modal.modal-wide', function (e) {
    var spin = function () {
      $(this).html(
        $(new Spinner().spin().el)
          .css({
            width: '100px', height: '100px',
            left: '50%', top: '50%',
            zIndex: calculate_spinner_z_index
          })
      ).one('loaded', function () {
        $(this).find('.source').each(spin);
      });
    };

    $(e.target).find('.modal-body .source').each(spin);
  });

  $body.on('click', '[data-toggle="list-remove"]', function (e) {
    e.preventDefault();
    $(this).closest('li').remove();
  });

  $body.on('click', '[data-toggle="list-select"]', function (e) {
    var $this;
    var $li;
    var target;
    var data;

    e.preventDefault();

    $this = $(this);
    $li = $this.closest('li');
    target = $li.closest('ul').data('list-target');

    if (target) {
      data = $.extend({}, $this.data('context') || {}, $this.data());
      $(target).tmpl_mergeitems([data]);
    }
  });

  $body.on('click', '[data-toggle="nested-dropdown"]', function (e) {
    var $parent = $(this).parent();
    var isActive = $parent.hasClass('open');
    if (!isActive) {
      $parent.toggleClass('open');
    }
    e.stopPropagation();
    e.preventDefault();
  });

  $('html').on('click.dropdown.data-api', function (e) {
    $('[data-toggle="nested-dropdown"]').parent().removeClass('open');
  });
});

jQuery(function ($) {
  function refresh_page() {
    setTimeout(can.proxy(window.location.reload, window.location), 10);
  }

  $body.on('ajax:complete', '[data-ajax-complete="refresh"]', refresh_page);
});

jQuery(function ($) {
  $body.on('ajax:success', '#helpedit form', function (e, data, status, xhr) {
    var $modal = $(this).closest('.modal');
    $modal.find('.modal-header h1').html(data.help.title);
    $modal.find('.modal-body .help-content').html(data.help.content);
    $modal.find('.modal-body #helpedit').collapse('hide');
  });
});

jQuery(function ($) {
  // Used in object_list sidebars (References, People, Categories)
  $body.on('modal:success', '.js-list-container-title a', function (e, data) {
    var $this = $(this);
    var $title = $this.closest('.js-list-container-title');
    var $span = $title.find('span');
    var $expander = $title.find('.expander').eq(0);

    $span.text('(' + (data.length || 0) + ')');

    if (data.length > 0) {
      $span.removeClass('no-object');
    } else {
      $span.addClass('no-object');
    }

    if (!$expander.hasClass('in')) {
      $expander.click();
    }
  });
});

jQuery(function ($) {
  function checkActive(notification_configs) {
    var inputs = $('.notify-wrap').find('input');
    var active_notifications = $.map(notification_configs, function (a) {
      if (a.enable_flag) {
        return a.notif_type;
      }
    });
    $.map(inputs, function (input) {
      // Handle the default case, in case notification objects are not set:
      if (notification_configs.length === 0) {
        input.checked = input.value === 'Email_Digest';
      } else {
        input.checked = active_notifications.indexOf(input.value) > -1;
      }
    });
  }
  function updateNotifications() {
    CMS.Models.NotificationConfig.findActive().then(checkActive);
    $body.off('click', '.user-dropdown > .dropdown-toggle', updateNotifications);
  }

  $body.on('click', '.user-dropdown > .dropdown-toggle', updateNotifications);

  // Don't close the dropdown if clicked on checkbox
  $body.on('click', '.notify-wrap', function (ev) {
    ev.stopPropagation();
  });

  $body.on('click', 'input[name=notifications]', function (ev, el) {
    var li = $(ev.target).closest('.notify-wrap');
    var inputs = li.find('input');
    var active = [];
    var email_now = li.find('input[value="Email_Now"]');
    var email_now_label = email_now.closest('label');
    var email_digest = li.find('input[value="Email_Digest"]');

    if (email_digest[0].checked) {
      email_now_label.removeClass('disabled');
      email_now.prop('disabled', false);
    } else if (!email_digest[0].checked) {// uncheck email_now
      email_now.prop('checked', false);
      email_now_label.addClass('disabled');
    }

    inputs.prop('disabled', true);
    active = $.map(inputs, function (input) {
      if (input.checked) {
        return input.value;
      }
    });
    CMS.Models.NotificationConfig.setActive(active).always(function (response) {
      email_digest.prop('disabled', false);
      if (email_digest[0].checked) {
        email_now.prop('disabled', false);
      }
    });
  });

  $body.on('click', '.clear-display-settings', function (e) {
    CMS.Models.DisplayPrefs.findAll().done(function (data) {
      var destroys = [];
      can.each(data, function (d) {
        d.unbind('change'); // forget about listening to changes.  we're going to refresh the page
        destroys.push(d.resetPagePrefs());
      });
      $.when.apply($, destroys).done(function () {
        GGRC.navigate();
      });
    });
  })
  .on('click', '.set-display-settings-default', function (e) {
    var page_token = getPageToken();
    CMS.Models.DisplayPrefs.findAll().done(function (data) {
      var destroys = [];
      can.each(data, function (d) {
        d.unbind('change'); // forget about listening to changes.  we're going to refresh the page
        destroys.push(d.setPageAsDefault(page_token));
      });
      $.when.apply($, destroys).done(function () {
        $body.trigger(
          'ajax:flash',
          {success: 'Saved page layout as default for ' + (page_token === 'dashboard' ? 'dashboard' : page_token)}
        );
      });
    });
  });
});

// Make all external links open in new window.
jQuery(function ($) {
  $body.on('click', 'a[href]:not([target])', function (e) {
    if (!e.isDefaultPrevented()) {
      if (/^http/.test(this.protocol) && this.hostname !== window.location.hostname) {
        e.preventDefault();
        window.open(this.href);
      }
    }
  });
});

function resize_areas(event, target_info_pin_height) {
  var $window = $(window);
  var $bar = $('.bar-v');
  var $footer = $('.footer');
  var $header = $('.header-content');
  var $innerNav = $('.inner-nav');
  var $lhnType = $('.lhn-type');
  var $lhsHolder = $('.lhs-holder');
  var $objectArea = $('.object-area');
  var $pin = $('.pin-content');
  var $topNav = $('.top-inner-nav');

  var winHeight = $window.height();
  var winWidth = $window.width();
  var lhsHeight = winHeight - 180; // new ui
  var footerMargin = lhsHeight + 130; // new UI
  var internavHeight = object_area_height();
  var internavWidth = $innerNav.width() || 0; // || 0 for pages without inner-nav
  var lhsWidth = $lhsHolder.width();
  var objectWidth = winWidth;

  $lhnType.css('width', lhsWidth);
  $lhsHolder.css('height', lhsHeight);
  $bar.css('height', lhsHeight);
  $footer.css('margin-top', footerMargin);
  $innerNav.css('height', internavHeight);
  $objectArea
    .css('margin-left', internavWidth)
    .css('height', internavHeight)
    .css('width', objectWidth);

  $objectArea.trigger('change');

  function object_area_height() {
    var height = winHeight - not_main_elements_height();
    var nav_pos = $topNav.css('top') ?
                Number($topNav.css('top').replace('px', '')) :
                0;

    if (nav_pos < $header.height()) {
      height -= $topNav.height();
    }

    return height;
  }

  function not_main_elements_height() {
    var margins = [$objectArea.css('margin-top'), $objectArea.css('margin-bottom'),
                     $objectArea.css('padding-top'), $objectArea.css('padding-bottom')]
              .map(function (margin) {
                if (!margin) {
                  margin = '0';
                }
                return Number(margin.replace('px', ''));
              })
              .reduce(function (m, h) {
                return m + h;
              }, 0);

    // the 5 gives user peace of mind they've reached bottom
    var UIHeight = [$topNav.height(), $header.height(),
                      $footer.height(),
                      margins, 5]
              .reduce(function (m, h) {
                return m + h;
              }, 0);

    return UIHeight;
  }
}

jQuery(function ($) {
  // Footer expander animation helper
  function expander(toggle, direction) {
    var $this = $(toggle);
    var $expander = $this.closest('div').find('.section-expander');
    var out = direction === 'out';
    var height = $expander.outerHeight();
    var width = $expander.outerWidth();
    var start = out ? 0 : width;
    var end = out ? width : 0;
    var duration = 500;
    var clip;

    if (out) {
      $this.filter(':not(.section-sticky)').fadeOut(200);
    }

    // Check for intermediate animation
    // Update the starting point and duration as appropriate
    if ($expander.is(':animated')) {
      $expander.stop();
      clip = $expander.css('clip').match(/^rect\(([0-9.-]+)px,?\s+([0-9.-]+)px,?\s+([0-9.-]+)px,?\s+([0-9.-]+)px\)$/);
      if (clip) {
        // Start or end is always zero, so we can use some shortcuts
        start = parseFloat(clip[2]);
        duration = ~~((end ? end - start : start) / width * duration);
      }
    }

    // Process animation
    $expander.css({
      display: 'inline-block',
      marginRight: end + 'px',
      clip: 'rect(0px, ' + start + 'px, ' + height + 'px, 0px)',
      left: $this.is('.section-sticky') ? $this.outerWidth() : 0
    }).animate({
      marginRight: start + 'px'
    }, {
      duration: duration,
      easing: 'easeInOutExpo',
      step: function (now, fx) {
        $(this).css('clip', 'rect(0px, ' + (width - now + (out ? start : end)) + 'px, ' + height + 'px, 0px)');
      },
      complete: function () {
        if (!out) {
          $this.filter(':not(.section-sticky)').fadeIn();
          $(this).hide();
        }
        $(this).css({
          marginRight: '0px',
          clip: 'auto'
        });
      }
    });

    // Queue the reverse on mouseout
    if (out) {
      $this.closest('li').one('mouseleave', function () {
        expander($this, 'in');
      });
    }
  }

  // Footer expander animations (verify that an expander exists)
  $body.on('mouseenter', '.section-add:has(+ .section-expander), .section-expander:visible:animated', function (e) {
    var $this = $(this);
    expander($this.hasClass('section-add') ? $this : $this.prev('.section-add'), 'out');
  });

  $body.on('click', '.show-long', function (e) {
    var $this = $(this);
    var $descField = $this.closest('.span12').find('.tree-description');
    $this.hide();
    $descField.removeClass('short');
  });

  // show/hide audit lead and firm
  $body.on('mouseover', '.ui-autocomplete li a', function (e) {
    var $this = $(this);
    $this.addClass('active');
    $this.closest('li').addClass('active');
  });
  $body.on('mouseleave', '.ui-autocomplete li a', function (e) {
    var $this = $(this);
    $this.removeClass('active');
    $this.closest('li').removeClass('active');
  });
});

function openMapperByElement(ev, disableMapper) {
  var btn = $(ev.currentTarget);
  var data = {};

  can.each(btn.data(), function (val, key) {
    data[can.camelCaseToUnderscore(key)] = val;
  });

  if (data.tooltip) {
    data.tooltip.hide();
  }

  if (!data.clickable) {
    ev.preventDefault();
  }

  import(/*webpackChunkName: "mapper"*/ './controllers/mapper/mapper').then(mapper => {
    mapper.ObjectMapper.openMapper(data, disableMapper, btn);
  });
}

$body.on('openMapper', (el, ev, disableMapper) => {
  openMapperByElement(ev, disableMapper);
});

$body.on('click', ['unified-mapper', 'unified-search']
  .map(val => '[data-toggle="' + val + '"]').join(', '), (ev, disable) => {
  openMapperByElement(ev, disable);
});

jQuery(window).on('load', resize_areas);
jQuery(window).on('resize', resize_areas);
