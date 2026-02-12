// ---------------- BMI CALCULATOR ----------------
function calculateBMI() {
    const height = parseFloat(document.getElementById("height").value);
    const weight = parseFloat(document.getElementById("weight").value);

    if (height > 0 && weight > 0) {
        const bmi = (weight / ((height / 100) ** 2)).toFixed(1);
        document.getElementById("bmi").value = bmi;
    }
}

// ---------------- QUICK PRESETS ----------------
function presetHealthy() {
    setValues(30, "Male", 118, 72, 92, 23.5);
}

function presetAtRisk() {
    setValues(45, "Female", 142, 88, 165, 29.4);
}

function presetHighRisk() {
    setValues(62, "Male", 170, 105, 230, 36.8);
}

function setValues(age, gender, bp, hr, sugar, bmi) {
    document.querySelector("input[name='age']").value = age;
    document.querySelector("select[name='gender']").value = gender;
    document.querySelector("input[name='bp']").value = bp;
    document.querySelector("input[name='hr']").value = hr;
    document.querySelector("input[name='sugar']").value = sugar;
    document.querySelector("input[name='bmi']").value = bmi;
}
