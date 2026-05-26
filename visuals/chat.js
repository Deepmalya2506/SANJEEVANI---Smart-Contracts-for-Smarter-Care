const sessionId = crypto.randomUUID();

async function sendMessage() {
    const input = document.getElementById("input").value;
    const chat = document.getElementById("chat");

    chat.innerHTML += `<div>🧑: ${input}</div>`;

    const res = await fetch("http://127.0.0.1:9001/chat", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            message: input,
            session_id: sessionId,
            hospital_id: "h1"   // 🔥 HOST CONTEXT
        })
    });

    const data = await res.json();

    if (data.approval_required) {
        showApproval(data.loan_proposal);
        return;
    }

    chat.innerHTML += `<div>🤖: ${data.reply}</div>`;

let currentApproval = null;

function showApproval(data) {
    currentApproval = data;
    document.getElementById("loanDetails").innerText =
        JSON.stringify(data, null, 2);

    document.getElementById("approvalModal").classList.remove("hidden");
}

async function approveLoan() {
    const res = await fetch("http://127.0.0.1:9001/approve", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            ...currentApproval,
            approved: true
        })
    });

    const data = await res.json();

    document.getElementById("chat").innerHTML +=
        `<div>✅ Loan Created: ${data.tx_hash}</div>`;

    closeModal();
}

function closeModal() {
    document.getElementById("approvalModal").classList.add("hidden");
}


}