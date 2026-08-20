const botao = document.getElementById("abrirConvite");
const transicao = document.getElementById("transicao");

botao.addEventListener("click", function () {

    // Ativa a tela de transição
    transicao.classList.add("ativa");

    // Aguarda a animação antes de trocar de página
    setTimeout(() => {

        window.location.href = "/apresentacao";

    }, 1200);

});