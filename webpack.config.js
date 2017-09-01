/*
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

const webpack = require('webpack');
const ExtractTextPlugin = require('extract-text-webpack-plugin');
const UglifyJSPlugin = require('uglifyjs-webpack-plugin');
const ManifestPlugin = require('webpack-manifest-plugin');
const CleanWebpackPlugin = require('clean-webpack-plugin');
const WebpackShellPlugin = require('webpack-shell-plugin');
const _ = require('lodash');
const path = require('path');
const ENV = process.env;

const STATIC_FOLDER = '/static/';

module.exports = function (env, argv) {
  const config = {
    entry: {
      vendor: 'entrypoints/vendor',
      dashboard: ['entrypoints/dashboard'].concat(getExtraModules())
        .concat(['entrypoints/dashboard/bootstrap'])
    },
    output: {
      filename: isProduction(env) ? '[name].[chunkhash].js' : '[name].js',
      sourceMapFilename: '[file].map',
      path: path.join(__dirname, './src/ggrc/static/'),
      publicPath: STATIC_FOLDER
    },
    module: {
      rules: [{
        test: /\.woff(\?v=\d+\.\d+\.\d+)?$/,
        loader: 'url?limit=10000&mimetype=application/font-woff'
      }, {
        test: /\.woff2(\?v=\d+\.\d+\.\d+)?$/,
        loader: 'url?limit=10000&mimetype=application/font-woff'
      }, {
        test: /\.ttf(\?v=\d+\.\d+\.\d+)?$/,
        loader: 'url?limit=10000&mimetype=application/octet-stream'
      }, {
        test: /\.eot(\?v=\d+\.\d+\.\d+)?$/,
        loader: 'file'
      }, {
        test: /\.svg(\?v=\d+\.\d+\.\d+)?$/,
        loader: 'url?limit=10000&mimetype=image/svg+xml'
      }, {
        test: /\.css$/,
        use: ExtractTextPlugin.extract({
          fallback: "style-loader",
          use: {
            loader: "css-loader",
            options: {url: false}
          }
        })
      }, {
        test: /\.s[ca]ss$/,
        use: ExtractTextPlugin.extract({
          use: [{
            loader: "css-loader"
          }, {
            loader: "sass-loader"
          }],
          fallback: "style-loader"
        })
      }, {
        test: /wysihtml5-0\.4\.0pre\.js$/,
        loader: 'exports-loader?wysihtml5'
      }, {
        test: require.resolve('jquery'),
        use: [{
          loader: 'expose-loader',
          options: 'jQuery'
        }, {
          loader: 'expose-loader',
          options: '$'
        }]
      }]
    },
    devtool: isDevelopment(env) ? 'eval' : 'source-map',
    resolve: {
      modules: ['node_modules', 'bower_components', 'third_party']
        .map(function (dir) {
          return path.join(__dirname, dir);
        }),
      alias: {
        'can': 'canjs/amd/can/',
        'entrypoints': './src/ggrc/assets/javascripts/entrypoints'
      }
    },
    plugins: [
      new ExtractTextPlugin({
        filename: '[name].css',
        allChunks: true
      }),
      new webpack.ProvidePlugin({
        $: 'jquery',
        jQuery: 'jquery',
        'window.jQuery': 'jquery',
        _: 'lodash',
        moment: 'moment'
      }),
      new webpack.DefinePlugin({
        GGRC_SETTINGS_MODULE: JSON.stringify(process.env.GGRC_SETTINGS_MODULE)
      }),
      new webpack.optimize.CommonsChunkPlugin({
        name: 'vendor'
      }),
      new webpack.IgnorePlugin(/^\.\/locale$/, /moment$/),
      new ManifestPlugin({
        publicPath: STATIC_FOLDER
      }),
      new WebpackShellPlugin({
        onBuildEnd:['cp src/ggrc/static/manifest.json src/ggrc/manifest.json']
      })
    ],
    stats: {
      errorDetails: true
    }
  };

  if (isProduction(env)) {
    config.plugins.push(new UglifyJSPlugin({
      sourceMap: true,
      output: {
        comments: false,
        beautify: false,
      }
    }));

    config.plugins.push(new CleanWebpackPlugin(['./src/ggrc/static/'], {
      exclude: ['images', 'fonts', 'favicon.ico']
    }));
  }

  return config;
};

function isProduction(env) {
  return env.production;
}

function isDevelopment(env) {
  return env.development;
}

function getExtraModules() {
  var modules = ENV.GGRC_SETTINGS_MODULE.split(' ');

  return _.compact(_.map(modules, function (module) {
    var name;
    if (/^ggrc/.test(module)) {
      name = module.split('.')[0];
    }

    if (!name) {
      return '';
    }
    return './src/' + name + '/assets/javascripts';
  }));
}
