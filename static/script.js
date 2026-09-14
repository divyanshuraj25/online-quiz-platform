
let timeLeft = 60;

const timerElement = document.getElementById("timer");

if (timerElement) {
    const countdown = setInterval(() => {
        timeLeft--;

        timerElement.textContent = timeLeft;

        if (timeLeft <= 0) {
            clearInterval(countdown);

            const quizForm = document.getElementById("quizForm");

            if (quizForm) {
                quizForm.submit();
            }
        }
    }, 1000);
}