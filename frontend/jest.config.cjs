module.exports = {
    moduleFileExtensions: ['js', 'json', 'vue', 'mjs'],
    transform: {
        '^.+\\.vue$': '@vue/vue3-jest',
        '^.+\\.js$': 'babel-jest',
        '^.+\\.mjs$': 'babel-jest',
        ".+\\.(css|styl|less|sass|scss|png|jpg|webp|ttf|woff|woff2)$": "jest-transform-stub"
    },
    testEnvironment: 'jest-environment-jsdom',
    coverageProvider: 'v8',
    coverageReporters: ['text', 'text-summary', 'json-summary'],
    resetModules: true,
    testEnvironmentOptions: {
        customExportConditions: ["node", "node-addons"],
    },
    testMatch: [
        '<rootDir>/test/**/*.test.js',
        '<rootDir>/test/**/*.spec.js',
    ],
    testPathIgnorePatterns: [
        '/node_modules/',
        '/e2e/',
    ],
    moduleNameMapper: {
        '^@/(.*)$': '<rootDir>/$1',
        '^~/service/CacheService$': '<rootDir>/service/CacheService.js',
        '^~/(.*)$': '<rootDir>/$1',
        '#imports': '<rootDir>/test/shared/nuxt-imports-mock.js',
        '\\.(css|less|scss|sass|png|jpg|webp|ttf|woff|woff2)$': 'jest-transform-stub',
    },
    transformIgnorePatterns: ['/node_modules/'],
    collectCoverageFrom: [
        'stores/**/*.js',
        'composables/**/*.js',
        'components/**/*.vue',
        'components/**/*.js',
        'utils/**/*.js',
        '!**/node_modules/**',
        '!components/**/index.js',
    ],
    coveragePathIgnorePatterns: [
        '/node_modules/',
        '/e2e/',
    ],
};
