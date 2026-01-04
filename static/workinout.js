// let lastCount = 0; // store previous count

// async function updateCounts(){
//   const res = await fetch("/get_counts");
//   const data = await res.json();

//   let count = 0;
//   if(exerciseMode===1) count = data.bicep_curl_left;
//   else if(exerciseMode===2) count = data.squat;
//   else if(exerciseMode===3) count = data.pushup;
//   else if(exerciseMode===4) count = data.jumping_jack;

//   const counterEl = document.getElementById("counter");

//   // Animate only if count changed
//   if(count !== lastCount){
//     // Add animation class
//     counterEl.classList.add("counter-update");

//     // Remove class after animation ends so it can trigger again
//     setTimeout(() => counterEl.classList.remove("counter-update"), 400);

//     // Smooth counting from last value to new value
//     animateValue(counterEl, lastCount, count, 400);
//     lastCount = count;
//   }
// }

// // Function to animate number increment
// function animateValue(element, start, end, duration) {
//   let startTime = null;

//   function step(currentTime) {
//     if (!startTime) startTime = currentTime;
//     let progress = currentTime - startTime;
//     let val = Math.floor(start + (end - start) * (progress / duration));
//     if (val > end) val = end;
//     element.innerText = "Exercise Count: " + val;
//     if (progress < duration) {
//       requestAnimationFrame(step);
//     } else {
//       element.innerText = "Exercise Count: " + end;
//     }
//   }
//   requestAnimationFrame(step);
// }

let exerciseMode = 1;
let isSending = false;

function setExercise(mode){
  if (isSending) return;
  isSending = true;

  exerciseMode = mode;

  fetch("/set_exercise", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ exercise_mode: mode })
  })
  .catch(err => console.error(err))
  .finally(() => isSending = false);
}

async function updateCounts(){
  try {
    const res = await fetch("/get_counts");
    if (!res.ok) return;

    const data = await res.json();

    let count = 0;
    if (exerciseMode === 1) count = data.bicep_curl_left;
    else if (exerciseMode === 2) count = data.squat;
    else if (exerciseMode === 3) count = data.pushup;
    else if (exerciseMode === 4) count = data.jumping_jack;

    const counterEl = document.getElementById("counter");
    if (counterEl) {
      counterEl.innerText = "Exercise Count: " + count;
    }
  } catch (err) {
    console.log("Waiting for backend...");
  }
}

setInterval(updateCounts, 500);
