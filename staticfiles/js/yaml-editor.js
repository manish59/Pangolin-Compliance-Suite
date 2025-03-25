/**
 * Reusable YAML Editor Component
 *
 * This script creates a YAML editor with Monaco or falls back to a plain textarea.
 * It can be attached to any container and textarea in a form.
 *
 * Usage:
 * 1. Include this script in your HTML
 * 2. Call YAMLEditor.init('containerId', 'textareaId') to initialize an editor
 *
 * Example:
 * YAMLEditor.init('config_data_editor', 'config_data');
 */

// Create a namespace to avoid polluting the global scope
const YAMLEditor = (function() {
    // Track all initialized editors
    const editors = {};

    // Load dependencies
    function loadDependencies(callback) {
        // Check for Monaco loader
        if (typeof require === 'undefined') {
            // Load Monaco loader
            const monacoScript = document.createElement('script');
            monacoScript.src = 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.34.1/min/vs/loader.min.js';
            monacoScript.onload = function() {
                // Configure Monaco paths
                require.config({
                    paths: { 'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.34.1/min/vs' }
                });

                // Check for jsyaml
                if (typeof jsyaml === 'undefined') {
                    const yamlScript = document.createElement('script');
                    yamlScript.src = 'https://cdnjs.cloudflare.com/ajax/libs/js-yaml/4.1.0/js-yaml.min.js';
                    yamlScript.onload = callback;
                    document.head.appendChild(yamlScript);
                } else {
                    callback();
                }
            };
            document.head.appendChild(monacoScript);
        } else {
            // Check for jsyaml
            if (typeof jsyaml === 'undefined') {
                const yamlScript = document.createElement('script');
                yamlScript.src = 'https://cdnjs.cloudflare.com/ajax/libs/js-yaml/4.1.0/js-yaml.min.js';
                yamlScript.onload = callback;
                document.head.appendChild(yamlScript);
            } else {
                callback();
            }
        }
    }

    // Create a simple textarea editor as fallback
    function createSimpleEditor(containerId, textareaId, options) {
        console.log(`Setting up simple textarea for ${containerId} as fallback`);

        const editorContainer = document.getElementById(containerId);
        const hiddenTextarea = document.getElementById(textareaId);

        if (!editorContainer || !hiddenTextarea) {
            console.error('Editor container or textarea not found');
            return null;
        }

        // Create a visible textarea
        const visibleTextarea = document.createElement('textarea');
        visibleTextarea.value = hiddenTextarea.value || options.defaultValue || '{}';
        visibleTextarea.className = 'w-full h-64 border border-gray-300 dark:border-gray-600 rounded-md font-mono p-2';
        visibleTextarea.style.resize = 'vertical';
        visibleTextarea.style.fontSize = options.fontSize || '14px';
        visibleTextarea.style.lineHeight = options.lineHeight || '1.5';

        // Sync changes to the hidden textarea
        visibleTextarea.addEventListener('input', function() {
            hiddenTextarea.value = visibleTextarea.value;
        });

        // Replace the editor container with our textarea
        editorContainer.innerHTML = '';
        editorContainer.appendChild(visibleTextarea);

        // Setup format button if jsyaml is available
        const formatButton = document.getElementById(`${textareaId}_format`);
        if (formatButton && typeof jsyaml !== 'undefined') {
            formatButton.addEventListener('click', function() {
                try {
                    const content = visibleTextarea.value;
                    const parsedYaml = jsyaml.load(content);
                    const formatted = jsyaml.dump(parsedYaml, {
                        indent: 2,
                        lineWidth: -1,
                        noRefs: true,
                        sortKeys: true
                    });
                    visibleTextarea.value = formatted;
                    hiddenTextarea.value = formatted;
                } catch (e) {
                    const validationMsg = document.getElementById(`${textareaId}_validation_message`);
                    if (validationMsg) {
                        validationMsg.textContent = `Error formatting YAML: ${e.message}`;
                        validationMsg.classList.add('text-red-600');
                    }
                }
            });
        }

        // Setup validate button if jsyaml is available
        const validateButton = document.getElementById(`${textareaId}_validate`);
        if (validateButton && typeof jsyaml !== 'undefined') {
            validateButton.addEventListener('click', function() {
                const validationMsg = document.getElementById(`${textareaId}_validation_message`);
                try {
                    jsyaml.load(visibleTextarea.value);
                    if (validationMsg) {
                        validationMsg.textContent = 'YAML is valid';
                        validationMsg.classList.remove('text-red-600');
                        validationMsg.classList.add('text-green-600');
                        setTimeout(() => { validationMsg.textContent = ''; }, 3000);
                    }
                } catch (e) {
                    if (validationMsg) {
                        validationMsg.textContent = `YAML error: ${e.message}`;
                        validationMsg.classList.remove('text-green-600');
                        validationMsg.classList.add('text-red-600');
                    }
                }
            });
        }

        return {
            type: 'simple',
            element: visibleTextarea,
            getValue: function() { return visibleTextarea.value; },
            setValue: function(value) {
                visibleTextarea.value = value;
                hiddenTextarea.value = value;
            }
        };
    }

    // Create Monaco editor
    function createMonacoEditor(containerId, textareaId, options) {
        return new Promise((resolve, reject) => {
            try {
                // Set timeout for Monaco loading
                const timeout = setTimeout(() => {
                    reject(new Error('Monaco editor load timeout'));
                }, options.timeout || 5000);

                // Load Monaco editor
                require(['vs/editor/editor.main'], function() {
                    clearTimeout(timeout);

                    const editorContainer = document.getElementById(containerId);
                    const textarea = document.getElementById(textareaId);

                    if (!editorContainer || !textarea) {
                        reject(new Error('Editor container or textarea not found'));
                        return;
                    }

                    try {
                        // Create Monaco editor
                        const editor = monaco.editor.create(editorContainer, {
                            value: textarea.value || options.defaultValue || '{}',
                            language: 'yaml',
                            theme: options.theme || 'vs',
                            automaticLayout: true,
                            minimap: { enabled: false },
                            lineNumbers: 'on',
                            scrollBeyondLastLine: false,
                            wordWrap: 'on',
                            wrappingIndent: 'indent',
                            tabSize: 2,
                            readOnly: false,
                            fontSize: options.fontSize || 14,
                            fontFamily: options.fontFamily || 'Consolas, "Courier New", monospace',
                            fontWeight: options.fontWeight || 'normal',
                            lineHeight: options.lineHeight || 20
                        });

                        // Ensure editor is not readonly
                        editor.updateOptions({ readOnly: false, tabIndex: 0 });

                        // Focus editor
                        setTimeout(() => { editor.focus(); }, 100);

                        // Update textarea when editor content changes
                        editor.onDidChangeModelContent(function() {
                            textarea.value = editor.getValue();
                        });

                        // Setup format button
                        const formatButton = document.getElementById(`${textareaId}_format`);
                        if (formatButton && typeof jsyaml !== 'undefined') {
                            formatButton.addEventListener('click', function() {
                                try {
                                    const content = editor.getValue();
                                    const parsedYaml = jsyaml.load(content);
                                    const formatted = jsyaml.dump(parsedYaml, {
                                        indent: 2,
                                        lineWidth: -1,
                                        noRefs: true,
                                        sortKeys: true
                                    });
                                    editor.setValue(formatted);
                                } catch (e) {
                                    const validationMsg = document.getElementById(`${textareaId}_validation_message`);
                                    if (validationMsg) {
                                        validationMsg.textContent = `Error formatting YAML: ${e.message}`;
                                        validationMsg.classList.add('text-red-600');
                                    }
                                }
                            });
                        }

                        // Setup validate button
                        const validateButton = document.getElementById(`${textareaId}_validate`);
                        if (validateButton && typeof jsyaml !== 'undefined') {
                            validateButton.addEventListener('click', function() {
                                const validationMsg = document.getElementById(`${textareaId}_validation_message`);
                                try {
                                    jsyaml.load(editor.getValue());
                                    if (validationMsg) {
                                        validationMsg.textContent = 'YAML is valid';
                                        validationMsg.classList.remove('text-red-600');
                                        validationMsg.classList.add('text-green-600');
                                        setTimeout(() => { validationMsg.textContent = ''; }, 3000);
                                    }
                                } catch (e) {
                                    if (validationMsg) {
                                        validationMsg.textContent = `YAML error: ${e.message}`;
                                        validationMsg.classList.remove('text-green-600');
                                        validationMsg.classList.add('text-red-600');
                                    }
                                }
                            });
                        }

                        resolve({
                            type: 'monaco',
                            editor: editor,
                            getValue: function() { return editor.getValue(); },
                            setValue: function(value) { editor.setValue(value); }
                        });

                    } catch (error) {
                        reject(error);
                    }
                }, function(error) {
                    clearTimeout(timeout);
                    reject(error);
                });
            } catch (error) {
                reject(error);
            }
        });
    }

    return {
        // Initialize a YAML editor
        init: function(containerId, textareaId, options = {}) {
            // Set default options
            const editorOptions = {
                fontSize: options.fontSize || 14,
                fontFamily: options.fontFamily || 'Consolas, "Courier New", monospace',
                lineHeight: options.lineHeight || 20,
                theme: options.theme || 'vs',
                timeout: options.timeout || 5000,
                defaultValue: options.defaultValue || '{}'
            };

            // Load dependencies and create editor
            loadDependencies(function() {
                createMonacoEditor(containerId, textareaId, editorOptions)
                    .then(editor => {
                        console.log(`Monaco editor initialized for ${containerId}`);
                        editors[containerId] = editor;
                    })
                    .catch(error => {
                        console.warn(`Failed to create Monaco editor for ${containerId}: ${error}. Falling back to simple editor.`);
                        editors[containerId] = createSimpleEditor(containerId, textareaId, editorOptions);
                    });
            });
        },

        // Get editor instance by container ID
        getEditor: function(containerId) {
            return editors[containerId];
        },

        // Get value from editor
        getValue: function(containerId) {
            const editor = editors[containerId];
            return editor ? editor.getValue() : null;
        },

        // Set value in editor
        setValue: function(containerId, value) {
            const editor = editors[containerId];
            if (editor) {
                editor.setValue(value);
                return true;
            }
            return false;
        }
    };
})();