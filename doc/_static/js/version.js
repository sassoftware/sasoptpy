function applyVersion() {
   var currentpath = window.location.pathname;
   var splitpath = currentpath.split('/');
   if (splitpath[1] === 'version') {
      var dropdown = document.getElementById('version_switch').children[0]
      dropdown.value = splitpath[2];
   } else {
      dropdown.value = 'latest';
   }
}

window.onload = applyVersion;

function goVersionHomepage(version) {
   if (version === 'latest') {
      window.location.href = '/index.html';
   } else {
      window.location.href = '/version/' + version + '/index.html';
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
      var pos = splitpath.indexOf('version')
      splitpath = splitpath.slice(pos+1);
   } else {
      splitpath = splitpath.slice(1);
   }
   var full_name = splitpath.join('/');
   
   var value = caller.options[index].value;
   if (index === 0) {
      var target_name = '/' + full_name;
   }
   else {
      var target_name = '/version/' + value + '/' + full_name;
   }
   console.log(target_name);
   var is_file_exists = fileExists(target_name);
   if (is_file_exists) {
      window.location.href = target_name;
   }
   else {
      goVersionHomepage(value);
   }
}
