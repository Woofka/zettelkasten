(function () {
  'use strict'

  var forms = document.querySelectorAll('.needs-validation')

  Array.prototype.slice.call(forms)
    .forEach(function (form) {
      form.addEventListener('submit', function (event) {
        if (!form.checkValidity()) {
          event.preventDefault()
          event.stopPropagation()
        }
        form.classList.add('was-validated')
      }, false)
    })
})()

function tagsValidation(input) {
  let tags = input.value.split('\n');
  for (let i = 0; i<tags.length; i++) {
    if (tags[i].trim().length > 50) {
      input.setCustomValidity('error');
      break;
    }
    input.setCustomValidity('');
  }
}
