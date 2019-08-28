(function() {
    "use strict";
    if (!window.hasOwnProperty("_glimpsebrowser")) {
        window._glimpsebrowser = {"initialized": {}};
    }

    if (window._glimpsebrowser.initialized["{{name}}"]) {
        return;
    }
    {{code}}
    window._glimpsebrowser.initialized["{{name}}"] = true;
})();
