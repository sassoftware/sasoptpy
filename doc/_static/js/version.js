function applyVersion() {
   var currentpath = window.location.pathname;
   var splitpath = currentpath.split('/');
   if (splitpath.includes('version')) {
      var dropdown = document.getElementById('version_switch').children[0];
      var pos = splitpath.indexOf('version') + 1;
      dropdown.value = splitpath[pos];
   } else {
      var dropdown = document.getElementById('version_switch').children[0];
      dropdown.value = 'latest';
   }
}

window.onload = applyVersion;

function goVersionHomepage(version) {
   if (version === 'latest') {
      window.location.href = window.location.origin + '/sasoptpy/index.html';
   } else {
      window.location.href = window.location.origin + '/sasoptpy/version/' + version + '/index.html';
   }
}

function getBaseName() {
   var path = window.location.pathname;
   var name = path.split(".");
   name.pop();
   name.join('.');
   return name;
}

function fileExists(fileName) {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', fileName, false);
    xhr.send();
    if (xhr.readyState === 4) {
       if (xhr.status === 200) {
          return true;
       }
    }
    return false;
}

function chooseVersion(caller) {
   var index = caller.options.selectedIndex;
   var currentpath = window.location.pathname;
   var splitpath = currentpath.split('/');
   
   if (splitpath.includes('version')) {
      var linkpath = splitpath.slice(splitpath.indexOf('version') + 2)
   } else {
      var linkpath = splitpath.slice(splitpath.indexOf('sasoptpy') + 1)
   }
   var regularlink = linkpath.join('/');
   
   var value = caller.options[index].value;
   if (index === 0) {
      var target_name =  regularlink;
   }
   else {
      var target_name = 'version/' + value + '/' + regularlink;
   }
   var actualtarget = window.location.origin + '/sasoptpy/' + target_name
   console.log(actualtarget);
   var is_file_exists = fileExists(actualtarget);
   if (is_file_exists) {
      window.location.href = actualtarget;
   }
   else {
      goVersionHomepage(value);
   }
}
