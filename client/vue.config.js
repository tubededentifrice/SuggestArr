const { defineConfig } = require('@vue/cli-service');
const webpack = require('webpack');
const fs = require('fs');
const yaml = require('yaml');
const path = require('path');

// Try to read SUBPATH from config if it exists
let subpath = '';
try {
  const configPath = path.resolve(__dirname, '../config/config_files/config.yaml');
  if (fs.existsSync(configPath)) {
    const configFile = fs.readFileSync(configPath, 'utf8');
    const config = yaml.parse(configFile);
    if (config && config.SUBPATH) {
      subpath = '/' + config.SUBPATH.replace(/^\/|\/$/g, '');
      console.log(`Using SUBPATH from config: ${subpath}`);
    }
  }
} catch (error) {
  console.warn('Could not read SUBPATH from config:', error.message);
}

module.exports = defineConfig({
  // Set the publicPath to the SUBPATH for correct asset URLs
  publicPath: subpath,
  
  // Define how the build process works
  configureWebpack: {
    plugins: [
      new webpack.DefinePlugin({
        __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: 'false',
        // Make SUBPATH available to Vue app
        __VUE_APP_SUBPATH__: JSON.stringify(subpath || ''),
      })
    ],
  }
});