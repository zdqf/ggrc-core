/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

describe('GGRC.Models.MapperModel', function () {
  'use strict';

  var mapper;
  var allTypes = [];
  var notMappableModels = [];
  var modules = {
    core: {
      models: [
        'AccessGroup',
        'Assessment',
        'AssessmentTemplate',
        'Audit',
        'Clause',
        'Contract',
        'Control',
        'DataAsset',
        'Facility',
        'Issue',
        'Market',
        'Objective',
        'OrgGroup',
        'Person',
        'Policy',
        'Process',
        'Product',
        'Program',
        'Project',
        'Regulation',
        'Section',
        'Standard',
        'System',
        'Vendor',
        'Risk',
        'Threat'
      ],
      notMappable: ['Assessment', 'Issue', 'AssessmentTemplate']
    },
    risk_assessments: {
      models: ['RiskAssessment'],
      notMappable: ['RiskAssessment']
    },
    workflows: {
      models: [
        'WorkflowTemplate'
      ],
      notMappable: [
        'WorkflowTemplate'
      ]
    }
  };
  var directives = ['Contract', 'Policy', 'Regulation', 'Standard'];
  var mappingRules;
  var filtered;
  var treeViewSettingsBackup;

  function getModelsFromGroups(groups, groupNames) {
    var models = [];
    groupNames.forEach(function (groupName) {
      var groupModels = groups[groupName].items.map(function (item) {
        return item.singular;
      });
      models = models.concat(groupModels);
    });
    return models;
  }

  Object.keys(modules).forEach(function (module) {
    allTypes = allTypes.concat(modules[module].models);
    notMappableModels = notMappableModels.concat(modules[module].notMappable);
  });

  filtered = _.difference(allTypes, notMappableModels);

  mappingRules = {
    AccessGroup: _.difference(filtered, ['AccessGroup']),
    Assessment: _.difference(filtered, ['Audit', 'Person', 'Program', 'Project']),
    AssessmentTemplate: _.difference(filtered, ['Audit', 'Person', 'Program',
      'Project']),
    Audit: _.difference(filtered, ['Audit', 'Person', 'Program', 'Project']),
    Clause: _.difference(filtered, ['Clause']),
    Contract: _.difference(filtered, directives),
    Control: filtered,
    DataAsset: filtered,
    Facility: filtered,
    Issue: _.difference(filtered, ['Audit', 'Person', 'Program', 'Project']),
    Market: filtered,
    Objective: filtered,
    OrgGroup: filtered,
    Person: _.difference(filtered, ['Person', 'Audit']),
    Policy: _.difference(filtered, directives),
    Process: filtered,
    Product: filtered,
    Program: _.difference(allTypes, ['Program'].concat(modules.core.notMappable,
      modules.workflows.notMappable)),
    Project: filtered,
    Regulation: _.difference(filtered, directives),
    Risk: filtered,
    RiskAssessment: [],
    Section: filtered,
    Standard: _.difference(filtered, directives),
    System: filtered,
    Threat: filtered,
    Vendor: filtered
  };

  beforeAll(function () {
    treeViewSettingsBackup = new can.Map(GGRC.tree_view);
    // init all modules
    can.each(GGRC.extensions, function (extension) {
      if (modules[extension.name] && extension.init_widgets) {
        extension.init_widgets();
      }
    });
  });

  afterAll(function () {
    GGRC.tree_view = treeViewSettingsBackup;
  });

  beforeEach(function () {
    mapper = GGRC.Models.MapperModel();
  });

  describe('get() for mapper.types', function () {
    beforeEach(function () {
      spyOn(mapper, 'initTypes')
        .and.returnValue('types');
    });

    it('returns types', function () {
      var result = mapper.attr('types');
      expect(result).toEqual('types');
    });
  });

  describe('get() for mapper.parentInstance', function () {
    beforeEach(function () {
      spyOn(CMS.Models, 'get_instance')
        .and.returnValue('parentInstance');
    });

    it('returns parentInstance', function () {
      var result = mapper.attr('parentInstance');
      expect(result).toEqual('parentInstance');
    });
  });

  describe('get() for mapper.useSnapshots', function () {
    it('use Snapshots if using in-scope model', function () {
      var result;
      spyOn(GGRC.Utils.Snapshots, 'isInScopeModel')
        .and.returnValue(true);
      result = mapper.attr('useSnapshots');
      expect(result).toEqual(true);
    });

    it('use Snapshots in case Assessment generation',
      function () {
        var result;
        spyOn(GGRC.Utils.Snapshots, 'isInScopeModel')
          .and.returnValue(false);
        mapper.attr('assessmentGenerator', true);
        result = mapper.attr('useSnapshots');
        expect(result).toEqual(true);
      });

    it('do not use Snapshots if not an in-scope model ' +
      'and not in assessment generation mode', function () {
      var result;
      spyOn(GGRC.Utils.Snapshots, 'isInScopeModel')
        .and.returnValue(false);
      mapper.attr('assessmentGenerator', false);
      result = mapper.attr('useSnapshots');
      expect(result).toEqual(false);
    });
  });

  describe('allowedToCreate() method', function () {
    it('returns true if not in a search mode and is not an in-scope model',
      function () {
        var result;
        mapper.attr('search_only', false);
        spyOn(GGRC.Utils.Snapshots, 'isInScopeModel')
          .and.returnValue(false);
        result = mapper.allowedToCreate();
        expect(result).toEqual(true);
      });

    it('returns false if in a search mode and is an in-scope model',
      function () {
        var result;
        mapper.attr('search_only', true);
        spyOn(GGRC.Utils.Snapshots, 'isInScopeModel')
          .and.returnValue(true);
        result = mapper.allowedToCreate();
        expect(result).toEqual(false);
      });

    it('returns false if in a search mode and is not an in-scope model',
      function () {
        var result;
        mapper.attr('search_only', true);
        spyOn(GGRC.Utils.Snapshots, 'isInScopeModel')
          .and.returnValue(false);
        result = mapper.allowedToCreate();
        expect(result).toEqual(false);
      });

    it('returns false if not in a search mode and is an in-scope model',
      function () {
        var result;
        mapper.attr('search_only', false);
        spyOn(GGRC.Utils.Snapshots, 'isInScopeModel')
          .and.returnValue(true);
        result = mapper.allowedToCreate();
        expect(result).toEqual(false);
      });
  });

  describe('showWarning() method', function () {
    it('returns false if is an in-scope model', function () {
      var result;
      spyOn(GGRC.Utils.Snapshots, 'isInScopeModel')
        .and.returnValue(true);
      result = mapper.showWarning();
      expect(result).toEqual(false);
    });

    it('returns false if is in assessment generation mode',
      function () {
        var result;
        spyOn(GGRC.Utils.Snapshots, 'isInScopeModel')
          .and.returnValue(false);
        mapper.attr('assessmentGenerator', true);
        result = mapper.showWarning();
        expect(result).toEqual(false);
      });

    it('returns false if is in a search mode', function () {
      var result;
      spyOn(GGRC.Utils.Snapshots, 'isInScopeModel')
        .and.returnValue(false);
      mapper.attr('search_only', true);
      result = mapper.showWarning();
      expect(result).toEqual(false);
    });

    it('returns true if source object is a Snapshot parent', function () {
      var result;
      spyOn(GGRC.Utils.Snapshots, 'isInScopeModel')
        .and.returnValue(false);
      spyOn(GGRC.Utils.Snapshots, 'isSnapshotParent')
        .and.callFake(function (v) {
          return v === 'o';
        });
      mapper.attr('object', 'o');
      mapper.attr('type', 't');
      result = mapper.showWarning();
      expect(result).toEqual(true);
    });

    it('returns true if is mapped object is a ' +
      'Snapshot parent', function () {
      var result;
      spyOn(GGRC.Utils.Snapshots, 'isInScopeModel')
        .and.returnValue(false);
      spyOn(GGRC.Utils.Snapshots, 'isSnapshotParent')
        .and.callFake(function (v) {
          return v === 't';
        });
      mapper.attr('object', 'o');
      mapper.attr('type', 't');
      result = mapper.showWarning();
      expect(result).toEqual(true);
    });
  });

  describe('prepareCorrectTypeFormat() method', function () {
    var cmsModel = {
      category: 'category',
      title_plural: 'title_plural',
      model_singular: 'model_singular',
      table_plural: 'table_plural',
      title_singular: 'title_singular'
    };
    var expectedResult = {
      category: 'category',
      name: 'title_plural',
      value: 'model_singular',
      plural: 'title_plural',
      singular: 'model_singular',
      table_plural: 'table_plural',
      title_singular: 'title_singular',
      isSelected: true
    };

    it('returns specified object', function () {
      var result;
      mapper.attr('type', 'model_singular');
      result = mapper.prepareCorrectTypeFormat(cmsModel);
      expect(result).toEqual(expectedResult);
    });

    it('converts models plural title to a snake_case', function () {
      var result;
      var cmsModel1 = _.assign({}, cmsModel, {
        title_plural: 'Title Plural'
      });
      mapper.attr('type', 'model_singular');
      result = mapper.prepareCorrectTypeFormat(cmsModel1);
      expect(result.plural).toEqual(expectedResult.plural);
    });

    it('is not selected if not equals the mapper type', function () {
      var result;
      mapper.attr('type', 'model_singular_');
      result = mapper.prepareCorrectTypeFormat(cmsModel);
      expect(result.isSelected).toEqual(false);
    });
  });

  describe('addFormattedType() method', function () {
    var groups;
    var type = {
      category: 'category'
    };

    beforeEach(function () {
      groups = {
        governance: {
          items: []
        },
        category: {
          items: []
        }
      };
      spyOn(mapper, 'prepareCorrectTypeFormat')
        .and.returnValue(type);
    });

    it('adds type to governance group if no group with category of this type',
      function () {
        groups.category = undefined;
        spyOn(GGRC.Utils, 'getModelByType')
          .and.returnValue({
            title_singular: 'title_singular'
          });
        mapper.addFormattedType('name', groups);
        expect(groups.governance.items[0]).toEqual(type);
      });

    it('adds type to group of category of this type if this group exist',
      function () {
        groups.governance = undefined;
        spyOn(GGRC.Utils, 'getModelByType')
          .and.returnValue({
            title_singular: 'title_singular'
          });
        mapper.addFormattedType('name', groups);
        expect(groups[type.category].items[0]).toEqual(type);
      });

    it('does nothing if cmsModel is not defined', function () {
      spyOn(GGRC.Utils, 'getModelByType');
      mapper.addFormattedType('name', groups);
      expect(groups.governance.items.length).toEqual(0);
      expect(groups[type.category].items.length).toEqual(0);
    });
    it('does nothing if singular title of cmsModel is not defined',
      function () {
        spyOn(GGRC.Utils, 'getModelByType')
          .and.returnValue({});
        mapper.addFormattedType('name', groups);
        expect(groups.governance.items.length).toEqual(0);
        expect(groups[type.category].items.length).toEqual(0);
      });
    it('does nothing if singular title of cmsModel is "Reference"',
      function () {
        spyOn(GGRC.Utils, 'getModelByType')
          .and.returnValue({
            title_singular: 'Reference'
          });
        mapper.addFormattedType('name', groups);
        expect(groups.governance.items.length).toEqual(0);
        expect(groups[type.category].items.length).toEqual(0);
      });
  });

  describe('getModelNamesList() method', function () {
    var object = 'object';
    var include = ['TaskGroupTask', 'TaskGroup',
      'CycleTaskGroupObjectTask'];
    beforeEach(function () {
      spyOn(GGRC.Mappings, 'getMappingList')
        .and.returnValue('mappingList');
    });

    it('returns names list excluding in-scope snapshots models' +
    ' if it is not search only', function () {
      var result = mapper.getModelNamesList(object);
      expect(result).toEqual('mappingList');
      expect(GGRC.Mappings.getMappingList)
        .toHaveBeenCalledWith(object, [], GGRC.Utils.Snapshots.inScopeModels);
    });

    it('returns names list if it is search only', function () {
      var result;
      mapper.attr('search_only', true);
      result = mapper.getModelNamesList(object);
      expect(result).toEqual('mappingList');
      expect(GGRC.Mappings.getMappingList)
        .toHaveBeenCalledWith(object, include, []);
    });
  });

  describe('initTypes() method', function () {
    var groups = {
      mockData: 123
    };

    beforeEach(function () {
      spyOn(mapper, 'getModelNamesList')
        .and.returnValue([321]);
      spyOn(mapper, 'addFormattedType');
    });

    it('returns groups', function () {
      var result;
      mapper.attr('typeGroups', groups);
      result = mapper.initTypes();
      expect(result).toEqual(groups);
      expect(mapper.addFormattedType)
        .toHaveBeenCalledWith(321, groups);
    });
  });

  describe('initTypes() method', function () {
    var initTypes;
    var EXPECTED_GROUPS = ['entities', 'business', 'governance'];
    var modelsForTests = _.difference(allTypes, [
      'WorkflowTemplate'
    ]);

    beforeEach(function () {
      initTypes = mapper.initTypes.bind(mapper);
      mapper.attr('search_only', false);
    });

    modelsForTests.forEach(function (type) {
      it('returns mappable types for ' + type, function () {
        var expectedModels = mappingRules[type];
        var result = initTypes(type);
        var resultGroups = Object.keys(result);
        var resultModels = getModelsFromGroups(result, EXPECTED_GROUPS);

        expect(EXPECTED_GROUPS).toEqual(resultGroups);
        expect(expectedModels.sort()).toEqual(resultModels.sort());
      });
    });
  });

  describe('getBindingName() method', function () {
    var instance;

    it('returns binding name with prefix "related_" if instance has no binding',
      function () {
        var result = mapper.getBindingName(instance, 'mock');
        expect(result).toEqual('related_mock');
      });

    it('returns binding name without prefix if instance has binding',
      function () {
        var result;
        instance = {
          has_binding: function () {
            return true;
          }
        };
        result = mapper.getBindingName(instance, 'mock');
        expect(result).toEqual('mock');
      });
  });

  describe('modelFromType() method', function () {
    it('returns undefined if no models', function () {
      var result = mapper.modelFromType('program');
      expect(result).toEqual(undefined);
    });

    it('returns model config by model value', function () {
      var result;
      var types = {
        governance: {
          items: [{
            value: 'v1'
          }, {
            value: 'v2'
          }, {
            value: 'v3'
          }]
        }
      };

      spyOn(mapper, 'initTypes')
        .and.returnValue(types);

      result = mapper.modelFromType('v2');
      expect(result).toEqual(types.governance.items[1]);
    });
  });

  describe('onSubmit() method', function () {
    it('sets true to mapper.afterSearch', function () {
      mapper.attr('afterSearch', false);
      mapper.onSubmit();
      expect(mapper.attr('afterSearch')).toEqual(true);
    });
  });
});
