function copyText(ev) {
    // Get the text field
    const activeId = ev.id;
    const copyText = document.getElementById(`input_${activeId}`);
    navigator.clipboard.writeText(copyText.value);
    copyText.select();
    copyText.setSelectionRange(0, 99999);

    const buttons = document.querySelectorAll('.button-addon')

    for (let btn of buttons) {
        btn.classList.remove('active')
        btn.innerText = 'Copy'
    }
    ev.classList.add('active')
    ev.innerText = 'Copied'
}