/**
 * This is a minimal config.
 *
 * If you need the full config, get it from here:
 * https://unpkg.com/browse/tailwindcss@latest/stubs/defaultConfig.stub.js
 */

 module.exports = {
    content: [
        /**
         * HTML. Paths to Django template files that will contain Tailwind CSS classes.
         */

        /*  Templates within theme app (<tailwind_app_name>/templates), e.g. base.html. */
        '../templates/**/*.html',

        /*
         * Main templates directory of the project (BASE_DIR/templates).
         * Adjust the following line to match your project structure.
         */
        '../../templates/**/*.html',

        /*
         * Templates in other django apps (BASE_DIR/<any_app_name>/templates).
         * Adjust the following line to match your project structure.
         */
        '../../**/templates/**/*.html',

        /**
         * JS: If you use Tailwind CSS in JavaScript, uncomment the following lines and make sure
         * patterns match your project structure.
         */
        /* JS 1: Ignore any JavaScript in node_modules folder. */
        // '!../../**/node_modules',
        /* JS 2: Process all JavaScript files in the project. */
        // '../../**/*.js',

        /**
         * Python: If you use Tailwind CSS classes in Python, uncomment the following line
         * and make sure the pattern below matches your project structure.
         */
        // '../../**/*.py'
    ],
    daisyui:{
        styled: true,
        base: true,
        themes: [
            {
                ebs: {
                    "primary": "#df643f",
                    "primary-focus": "#c44820",
                    "primary-content": "#ffffff",
                    "base-100": "#ffffff",
                    "base-200": "#fafafa",
                    "base-300": "#d6d6d6",
                    "secondary": "#565A63",
                    "accent": "#8C94A3",
                    "neutral": "#131416",
                    "error": "#FD8B90",
                    "info": "#7CB8FF",
                    "success": "#B0F28B",
                    "warning": "#FDD865",
                },
            },
        ],
    },
    theme: {

        extend: {
            fontFamily: {
                lora: ["Lora", "serif"],
                nunito: ["Nunito Sans", "sans-serif"],
                mono: ["Ubuntu Mono", "monospace"],
            },
        },
    },
    plugins: [
        /**
         * '@tailwindcss/forms' is the forms plugin that provides a minimal styling
         * for forms. If you don't like it or have own styling for forms,
         * comment the line below to disable '@tailwindcss/forms'.
         */
        // require('@tailwindcss/forms'),
        require('@tailwindcss/typography'),
        require('@tailwindcss/line-clamp'),
        require('@tailwindcss/aspect-ratio'),
        require('daisyui'),
    ],
}
