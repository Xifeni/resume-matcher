import eslint from '@eslint/js';
import tseslint from 'typescript-eslint';
import pluginVue from 'eslint-plugin-vue';

export default tseslint.config(
  // Базовые рекомендованные правила JS
  eslint.configs.recommended,

  // Рекомендованные правила TypeScript
  ...tseslint.configs.recommended,

  // Рекомендованные правила для Vue 3 (Flat config)
  ...pluginVue.configs['flat/recommended'],

  // Настройка парсера для .vue файлов, чтобы он понимал TypeScript
  {
    files: ['*.vue', '**/*.vue'],
    languageOptions: {
      parserOptions: {
        parser: tseslint.parser,
        sourceType: 'module',
        extraFileExtensions: ['.vue'],
      },
    },
  },

  // Глобальные игнорируемые папки (замена старого .eslintignore)
  {
    ignores: ['dist/**', 'node_modules/**', '.pnp.*'],
  },

  // Ваши кастомные правила
  {
    rules: {
      // Отключаем требование мульти-словных имен компонентов (на ваше усмотрение)
      'vue/multi-word-component-names': 'off',

      // Пример: разрешаем использование any (лучше включить в строгих проектах)
      '@typescript-eslint/no-explicit-any': 'warn',

      // В Vue 3 + TS иногда полезно отключить это правило,
      // так как компилятор сам проверяет неиспользуемые переменные
      '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
    },
  }
);
