module.exports = {
    presets: [
      ['@babel/preset-env', { targets: { node: 'current' } }]
    ],
    plugins: [
      // Replace import.meta.* with undefined so jest (CJS) can parse ESM meta
      function importMetaPlugin() {
        return {
          visitor: {
            MemberExpression(path) {
              if (
                path.node.object.type === 'MetaProperty' &&
                path.node.object.meta.name === 'import' &&
                path.node.object.property.name === 'meta'
              ) {
                path.replaceWith({ type: 'Identifier', name: 'undefined' });
              }
            },
          },
        };
      },
    ],
  };
