# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

import csv
from StringIO import StringIO
import chardet

from ggrc.models.reflection import AttributeInfo
from ggrc.converters import get_exportables
from ggrc.converters.column_handlers import model_column_handlers
from ggrc.converters.handlers import handlers


def get_object_column_definitions(object_class):
  """Attach additional info to attribute definitions.

  Fetches the attribute info (_aliases) for the given object class and adds
  additional data (handler class, validator function, default value) )needed
  for imports.

  Args:
    object_class (db.Model): Model for which we want to get column definitions
      for imports.

  Returns:
    dict: Updated attribute definitions dict with additional data.
  """
  attributes = AttributeInfo.get_object_attr_definitions(object_class)
  column_handlers = model_column_handlers(object_class)
  for key, attr in attributes.iteritems():
    handler_key = attr.get("handler_key", key)
    # check full handler keys
    handler = column_handlers.get(handler_key)
    if not handler:
      # check handler key prefixes
      handler = column_handlers.get(handler_key.split(":")[0])
    if not handler:
      # use default handler
      handler = handlers.ColumnHandler
    validator = None
    default = None
    if attr["type"] == AttributeInfo.Type.PROPERTY:
      validator = getattr(object_class, "validate_{}".format(key), None)
      default = getattr(object_class, "default_{}".format(key), None)

    attr["handler"] = attr.get("handler", handler)
    attr["validator"] = attr.get("validator", validator)
    attr["default"] = attr.get("default", default)
  return attributes


def get_column_order(columns):
  return AttributeInfo.get_column_order(columns)


def generate_csv_string(csv_data):
  """ Turn 2d string array into a string representing a csv file """
  output_buffer = StringIO()
  writer = csv.writer(output_buffer)

  csv_data = equalize_array(csv_data)
  csv_data = utf_8_encode_array(csv_data)

  for row in csv_data:
    writer.writerow(row)

  body = output_buffer.getvalue()
  output_buffer.close()
  return body


def extract_relevant_data(csv_data):
  """ Split csv data into data and metadata """
  striped_data = [[unicode.strip(c) for c in line]
                  for line in csv_data]  # noqa
  transpose_data = zip(*striped_data[1:])
  non_empty = [d for d in transpose_data if any(d)]
  data = zip(*non_empty[1:])
  column_definitions = list(data.pop(0))
  data = [list(d) for d in data]
  return column_definitions, data


def equalize_array(array):
  """ Expand all rows of 2D array to the same length """
  if len(array) == 0:
    return array
  max_length = max([len(i) for i in array])
  for row in array:
    diff = max_length - len(row)
    row.extend([""] * diff)
  return array


def split_array(csv_data):
  """ Split array by empty lines """
  data_blocks = []
  offsets = []
  current_block = None
  for offset, line in enumerate(csv_data):
    if sum([len(l) for l in line]) > 0:
      if current_block is None:
        offsets.append(offset)
        data_blocks.append([])
        current_block = len(data_blocks) - 1
      data_blocks[current_block].append(line)
    else:
      current_block = None

  return offsets, data_blocks


def generate_2d_array(width, height, value=None):
  """ Generate 2D array of size width x height """
  return [[value for _ in range(width)] for _ in range(height)]


def csv_reader(csv_data, dialect=csv.excel, **kwargs):
  """ Reader for csv files """
  reader = csv.reader(utf_8_encoder(csv_data), dialect=dialect, **kwargs)
  for row in reader:
    yield [unicode(cell, 'utf-8') for cell in row]  # noqa


def read_csv_file(csv_file):
  """ Get full string representation of the csv file """
  return [row for row in csv_reader(csv_file)]


def utf_8_encode_array(array):
  """ encode 2D array to utf8 """
  return [[val.encode("utf-8") for val in line] for line in array]


def utf_8_encoder(csv_data):
  """This function is a generator that attempts to encode the string as utf-8.
  It is assumed that the data is likely to be encoded in ascii. If encoding
  fails, however, the function will attempt to guess the encoding and convert
  it to utf-8.
  Guessing is only done when a line fails to encode as there may be characters
  further in the stream that aren't valid ascii and encoding is performed per
  line yielded; guessing is the fallback on a per-line basis.
  """
  for line in csv_data:
    try:
      yield line.decode('utf-8').encode('utf-8')
    except UnicodeDecodeError:
      encoding_guess = chardet.detect(line)['encoding']
      yield line.decode(encoding_guess).encode('utf-8')
    except UnicodeEncodeError:
      yield line.encode('utf-8')


def count_objects(csv_data):
  """Count objects in csv data"""
  exportables = get_exportables()
  offsets, data_blocks = split_array(csv_data)
  counts = {}
  for _, data in zip(offsets, data_blocks):
    if len(data) < 2:
      continue  # empty block
    class_name = data[1][0].strip().lower()
    object_class = exportables.get(class_name)
    counts[object_class.__name__] = len(data) - 2
  return counts


def get_export_filename(objects, current_time):
  """Generate export file name"""
  object_names = "_".join([obj['object_name'] for obj in objects])
  return "{}_{}.csv".format(object_names, current_time)
