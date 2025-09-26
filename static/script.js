const rangeInput = document.querySelectorAll(".range-input input"),
valueInput = document.querySelectorAll(".value-input input"),
progress = document.querySelector(".slider .progress");

let valGap = 10

// Updates numerical value when slider value is changed
valueInput.forEach((input) => {
    input.addEventListener("input", e=>{
        // Getting input values (Min and Max), then parsing them to Integers
        let minVal = parseInt(valueInput[0].value),
        maxVal = parseInt(valueInput[1].value);
        
        if((maxVal - minVal >= valGap) && maxVal <= 1200){
            // Checks if minimum input event is triggrered
            if(e.target.className === "min-input"){
                rangeInput[0].value = minVal;
                progress.style.left = (minVal / rangeInput[0].max) * 100 + "%";
            }
            else{
                rangeInput[1].value = maxVal;
                progress.style.right = 100 - (maxVal / rangeInput[1].max) * 100 + "%";
            }
        }
    });
});

// Updates numerical value when slider value is changed
rangeInput.forEach((input) => {
    input.addEventListener("input", e=>{
        // Getting range values (Min and Max), then parsing them to Integers
        let minVal = parseInt(rangeInput[0].value),
        maxVal = parseInt(rangeInput[1].value);
        
        if(maxVal - minVal < valGap){
            // Checks if minimun input event is triggrered
            if(e.target.className === "min-range"){
                rangeInput[0].value = maxVal - valGap;
            }
            else{
                rangeInput[1].value = minVal + valGap;
            }
        }
        else{
            valueInput[0].value = minVal;
            valueInput[1].value = maxVal;
            progress.style.left = (minVal / rangeInput[0].max) * 100 + "%";
            progress.style.right = 100 - (maxVal / rangeInput[1].max) * 100 + "%";
        }
    });
});

function captureValues() {
    const minInput = document.getElementById("min-input").value;
    const maxInput = document.getElementById("max-input").value;

    console.log(`Sending values - Min: ${minInput}, Max: ${maxInput}`);

    fetch(`/receive`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        body: JSON.stringify({
            minimumValue: minInput,
            maximumValue: maxInput
        })
    })
    .then(response => response.json())  // Wait for the response and parse it as JSON
    .then(data => {
        console.log(data.message);  // Log the message returned from the server
    })
    .catch(error => {
        console.error('Error:', error);  // Handle any errors
    });
}

document.querySelector('.min-range').addEventListener('input', function() {
    document.getElementById('min-input').value = this.value;
    captureValues();
});

document.querySelector('.max-range').addEventListener('input', function() {
    document.getElementById('max-input').value = this.value;
    captureValues();
});