(function () {
  "use strict";

  var scheduleDays = typeof scheduleDays !== "undefined" ? scheduleDays : ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
  var userSchedule = typeof userSchedule !== "undefined" ? userSchedule : {};

  // Nav toggle (mobile)
  var navToggle = document.querySelector(".nav-toggle");
  var navLinks = document.querySelector(".nav-links");
  if (navToggle && navLinks) {
    navToggle.addEventListener("click", function () {
      navLinks.classList.toggle("is-open");
    });
  }

  // Schedule page: card click -> open exercises panel
  var scheduleGrid = document.getElementById("schedule-grid");
  var homeScheduleGrid = document.getElementById("home-schedule-grid");
  var exercisesPanel = document.getElementById("exercises-panel");
  var exercisesDayTitle = document.getElementById("exercises-day-title");
  var exercisesList = document.getElementById("exercises-list");
  var closeExercisesBtn = document.getElementById("close-exercises");

  if (scheduleGrid && exercisesPanel) {
    scheduleGrid.addEventListener("click", function (e) {
      var card = e.target.closest(".schedule-card");
      if (!card) return;
      var day = card.getAttribute("data-day");
      var muscleEl = card.querySelector(".schedule-muscle");
      var muscleGroup = muscleEl ? muscleEl.textContent.trim().toLowerCase() : "";
      if (muscleGroup === "rest day" || muscleGroup === "rest") muscleGroup = "";
      openExercisesPanel(day, muscleGroup);
    });
  }

  if (homeScheduleGrid && !window.USER_LOGGED_IN) {
    // Dummy muscle groups for demo preview cards
    var demo = {
      Monday: "chest",
      Tuesday: "back",
      Wednesday: "biceps",
      Thursday: "triceps",
      Friday: "shoulders",
      Saturday: "legs",
      Sunday: "core"
    };
    homeScheduleGrid.querySelectorAll(".schedule-card").forEach(function (card) {
      var day = card.getAttribute("data-day");
      var mg = demo[day] || "chest";
      var el = card.querySelector(".schedule-muscle");
      if (el) el.textContent = mg;
    });
  }

  function openExercisesPanel(day, muscleGroup) {
    exercisesDayTitle.textContent = day;
    exercisesList.innerHTML = "<p class=\"loading\">Loading…</p>";
    exercisesPanel.classList.remove("hidden");

    if (!muscleGroup) {
      exercisesList.innerHTML = "<p class=\"muted\">Rest day — no exercises.</p>";
      return;
    }

    fetch("/api/exercises?muscle_group=" + encodeURIComponent(muscleGroup))
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data && data.error) {
          exercisesList.innerHTML = "<p class=\"muted\">" + (data.error || "Error loading exercises.") + "</p>";
          return;
        }
        var list = Array.isArray(data) ? data : [];
        if (list.length === 0) {
          exercisesList.innerHTML = "<p class=\"muted\">No exercises for this muscle group yet.</p>";
          return;
        }
        exercisesList.innerHTML = list.map(function (ex) {
          var img = (ex.image_url || "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=400&h=240&fit=crop").replace(/&/g, "&amp;");
          var name = (ex.name || "Exercise").replace(/</g, "&lt;");
          var hasVideo = ex.video_url;
          var exJson = JSON.stringify(ex).replace(/"/g, "&quot;");
          return (
            "<div class=\"exercise-card\" data-exercise=\"" + exJson + "\">" +
              "<div class=\"exercise-card-image\">" +
                "<img src=\"" + img + "\" alt=\"\" loading=\"lazy\" />" +
                (hasVideo ? "<div class=\"play-overlay\"><span>▶</span></div>" : "") +
              "</div>" +
              "<div class=\"exercise-card-name\">" + name + "</div>" +
              (window.USER_LOGGED_IN && hasVideo ? (
                "<form class=\"log-workout-form\" data-exercise-id=\"" + (ex.id || "") + "\">" +
                  "<input type=\"number\" name=\"duration_minutes\" placeholder=\"Min\" min=\"1\" max=\"180\" />" +
                  "<input type=\"number\" name=\"calories_burned\" placeholder=\"Cal\" min=\"0\" />" +
                  "<button type=\"submit\" class=\"btn btn-primary\">Log</button>" +
                "</form>"
              ) : "") +
            "</div>"
          );
        }).join("");

        // Clicks: image -> video; form submit -> log
        exercisesList.querySelectorAll(".exercise-card").forEach(function (el) {
          var ex = null;
          try { ex = JSON.parse(el.getAttribute("data-exercise")); } catch (_) {}
          var imgWrap = el.querySelector(".exercise-card-image");
          if (imgWrap && ex) {
            imgWrap.addEventListener("click", function () {
              openImageThenVideo(ex);
            });
          }
          var form = el.querySelector(".log-workout-form");
          if (form) {
            form.addEventListener("submit", function (e) {
              e.preventDefault();
              var fd = new FormData(form);
              var payload = {
                exercise_id: form.getAttribute("data-exercise-id"),
                duration_minutes: parseInt(fd.get("duration_minutes"), 10) || 0,
                calories_burned: parseInt(fd.get("calories_burned"), 10) || 0
              };
              fetch("/api/workout-logs", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
              }).then(function (r) {
                if (r.ok) { form.querySelector('input[name="duration_minutes"]').value = ""; form.querySelector('input[name="calories_burned"]').value = ""; }
              });
            });
          }
        });
      })
      .catch(function () {
        exercisesList.innerHTML = "<p class=\"muted\">Failed to load exercises.</p>";
      });
  }

  if (closeExercisesBtn && exercisesPanel) {
    closeExercisesBtn.addEventListener("click", function () { exercisesPanel.classList.add("hidden"); });
  }

  // Video modal
  var videoModal = document.getElementById("video-modal");
  var exerciseVideo = document.getElementById("exercise-video");
  var videoTitleEl = document.getElementById("video-title");
  var closeVideoBtn = document.getElementById("close-video");
  var imageModal = document.getElementById("image-modal");
  var exerciseImage = document.getElementById("exercise-image");
  var imageTitleEl = document.getElementById("image-title");
  var closeImageBtn = document.getElementById("close-image");

  var pendingVideoTimer = null;

  function openVideoModal(ex, delayMs) {
    if (!ex || !ex.video_url) return;
    delayMs = typeof delayMs === "number" ? delayMs : 2000;
    videoTitleEl.textContent = ex.name || "";
    exerciseVideo.src = ex.video_url;
    // Play after delay
    setTimeout(function () {
      try { exerciseVideo.play(); } catch (e) {}
    }, delayMs);
    if (videoModal) videoModal.classList.remove("hidden");
  }

  function openImageModal(ex) {
    if (!ex || !ex.image_url || !imageModal) return;
    if (imageTitleEl) imageTitleEl.textContent = ex.name || "";
    if (exerciseImage) { exerciseImage.src = ex.image_url; exerciseImage.alt = ex.name || "Exercise"; }
    imageModal.classList.remove("hidden");
  }

  function openImageThenVideo(ex) {
    // Always show image first. If video exists, open video after 3s of image showing.
    if (pendingVideoTimer) { clearTimeout(pendingVideoTimer); pendingVideoTimer = null; }
    openImageModal(ex);
    if (ex && ex.video_url) {
      pendingVideoTimer = setTimeout(function () {
        // If image modal is still open, switch to video.
        if (imageModal && !imageModal.classList.contains("hidden")) {
          closeImageModal();
          openVideoModal(ex, 0);
        }
        pendingVideoTimer = null;
      }, 3000);
    }
  }

  function exerciseFromTile(tile) {
    if (!tile) return null;
    // Prefer dataset attrs (robust), fallback to JSON if present
    var ds = tile.dataset || {};
    if (ds && (ds.imageUrl || ds.videoUrl || ds.name)) {
      return {
        id: ds.id,
        name: ds.name,
        image_url: ds.imageUrl,
        video_url: ds.videoUrl || ""
      };
    }
    var raw = tile.getAttribute("data-ex");
    if (raw) {
      try { return JSON.parse(raw); } catch (e) { return null; }
    }
    return null;
  }

  function closeVideoModal() {
    if (exerciseVideo) { exerciseVideo.pause(); exerciseVideo.src = ""; }
    if (videoModal) videoModal.classList.add("hidden");
  }

  function closeImageModal() {
    if (pendingVideoTimer) { clearTimeout(pendingVideoTimer); pendingVideoTimer = null; }
    if (exerciseImage) { exerciseImage.src = ""; }
    if (imageModal) imageModal.classList.add("hidden");
  }

  if (closeVideoBtn) closeVideoBtn.addEventListener("click", closeVideoModal);
  if (videoModal) {
    videoModal.querySelector(".modal-backdrop").addEventListener("click", closeVideoModal);
  }
  if (closeImageBtn) closeImageBtn.addEventListener("click", closeImageModal);
  if (imageModal) {
    imageModal.querySelector(".modal-backdrop").addEventListener("click", closeImageModal);
  }

  // Save schedule (used on Profile + Schedule page)
  function bindScheduleSave(buttonId, gridId) {
    var btn = document.getElementById(buttonId);
    var grid = document.getElementById(gridId);
    if (!btn || !grid) return;
    btn.addEventListener("click", function () {
      var selects = grid.querySelectorAll(".schedule-select");
      var promises = [];
      selects.forEach(function (sel) {
        var day = sel.getAttribute("data-day");
        var muscleGroup = sel.value || "rest";
        promises.push(
          fetch("/api/schedule", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ day: day, muscle_group: muscleGroup })
          })
        );
      });
      Promise.all(promises).then(function () {
        alert("Schedule saved.");
        if (typeof window.location !== "undefined") window.location.reload();
      }).catch(function () { alert("Failed to save."); });
    });
  }

  bindScheduleSave("save-schedule-btn", "schedule-edit-grid"); // profile page
  bindScheduleSave("save-schedule-btn-schedule", "schedule-edit-grid-schedule"); // schedule page

  // Weekly analysis
  if (window.WEEKLY_ANALYSIS) {
    fetch("/api/weekly-stats")
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data && data.error) return;
        var elMin = document.getElementById("stat-minutes");
        var elCal = document.getElementById("stat-calories");
        var elEx = document.getElementById("stat-exercises");
        if (elMin) elMin.textContent = data.total_minutes != null ? data.total_minutes : 0;
        if (elCal) elCal.textContent = data.total_calories != null ? data.total_calories : 0;
        if (elEx) elEx.textContent = data.exercises_completed != null ? data.exercises_completed : 0;

        var byDay = data.by_day || {};
        var daysOrder = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
        var weekStart = data.week_start ? data.week_start.slice(0, 10) : "";
        var labels = [];
        var minutesData = [];
        for (var i = 0; i < 7; i++) {
          var d = new Date(weekStart);
          d.setDate(d.getDate() + i);
          var key = d.toISOString().slice(0, 10);
          labels.push(key);
          minutesData.push(byDay[key] ? (byDay[key].minutes || 0) : 0);
        }
        var canvas = document.getElementById("weekly-chart");
        if (canvas && typeof Chart !== "undefined") {
          new Chart(canvas.getContext("2d"), {
            type: "bar",
            data: {
              labels: labels,
              datasets: [{ label: "Minutes", data: minutesData, backgroundColor: "rgba(0, 212, 170, 0.6)" }]
            },
            options: {
              responsive: true,
              scales: { y: { beginAtZero: true } }
            }
          });
        }
      });

    fetch("/api/workout-logs")
      .then(function (r) { return r.json(); })
      .then(function (logs) {
        var list = document.getElementById("logs-list");
        if (!list) return;
        if (!Array.isArray(logs) || logs.length === 0) {
          list.innerHTML = "<li>No workouts yet.</li>";
          return;
        }
        list.innerHTML = logs.slice(0, 10).map(function (l) {
          var date = (l.workout_date || "").slice(0, 10);
          var name = (l.exercises && l.exercises.name) ? l.exercises.name : "Workout";
          return "<li>" + date + " — " + name + " <span>" + (l.duration_minutes || 0) + " min, " + (l.calories_burned || 0) + " cal</span></li>";
        }).join("");
      });
  }

  // Calories calculator
  var caloriesForm = document.getElementById("calories-form");
  var caloriesResult = document.getElementById("calories-result");
  var calMaintenance = document.getElementById("cal-maintenance");
  if (caloriesForm && caloriesResult && calMaintenance) {
    caloriesForm.addEventListener("submit", function (e) {
      e.preventDefault();
      var weight = parseFloat(document.getElementById("cal-weight").value) || 70;
      var height = parseFloat(document.getElementById("cal-height").value) || 170;
      var age = parseInt(document.getElementById("cal-age").value, 10) || 30;
      var activity = parseFloat(document.getElementById("cal-activity").value) || 1.55;
      var male = document.querySelector("input[name=\"cal-sex\"][value=\"male\"]").checked;
      var bmr = male
        ? 10 * weight + 6.25 * height - 5 * age + 5
        : 10 * weight + 6.25 * height - 5 * age - 161;
      var tdee = Math.round(bmr * activity);
      calMaintenance.textContent = tdee;
      caloriesResult.classList.remove("hidden");
    });
  }

  // Home: demo exercise tiles
  var homeExercises = document.getElementById("home-exercises");
  if (homeExercises) {
    homeExercises.innerHTML = "<p class=\"muted\">Loading exercises…</p>";
    fetch("/api/exercises")
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var list = Array.isArray(data) ? data : [];
        if (!list.length) {
          homeExercises.innerHTML = "<p class=\"muted\">No exercises yet. Run the Supabase seed in supabase_schema.sql.</p>";
          return;
        }
        homeExercises.innerHTML = list.slice(0, 8).map(function (ex) {
          var img = (ex.image_url || "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=400&h=240&fit=crop").replace(/&/g, "&amp;");
          var name = (ex.name || "Exercise").replace(/</g, "&lt;");
          var mg = (ex.muscle_group || "").replace(/</g, "&lt;");
          return (
            "<div class=\"exercise-tile\">" +
              "<img src=\"" + img + "\" alt=\"\" loading=\"lazy\" />" +
              "<div class=\"exercise-tile-body\">" +
                "<h4>" + name + "</h4>" +
                "<div class=\"meta\">" + mg + "</div>" +
              "</div>" +
            "</div>"
          );
        }).join("");
      })
      .catch(function () {
        homeExercises.innerHTML = "<p class=\"muted\">Failed to load exercises.</p>";
      });
  }

  // BMI calculator
  var bmiForm = document.getElementById("bmi-form");
  var bmiResult = document.getElementById("bmi-result");
  var bmiValue = document.getElementById("bmi-value");
  var bmiCategory = document.getElementById("bmi-category");
  if (bmiForm && bmiResult && bmiValue && bmiCategory) {
    bmiForm.addEventListener("submit", function (e) {
      e.preventDefault();
      var weight = parseFloat(document.getElementById("bmi-weight").value) || 70;
      var heightCm = parseFloat(document.getElementById("bmi-height").value) || 170;
      var heightM = heightCm / 100;
      if (!heightM) return;
      var bmi = weight / (heightM * heightM);
      var rounded = Math.round(bmi * 10) / 10;
      var category = "";
      if (bmi < 18.5) category = "Underweight";
      else if (bmi < 25) category = "Normal weight";
      else if (bmi < 30) category = "Overweight";
      else category = "Obesity";
      bmiValue.textContent = rounded.toFixed(1);
      bmiCategory.textContent = category;
      bmiResult.classList.remove("hidden");
    });
  }

  // Diet day screen: Edit diet plan button, Cancel, Save (update cards on success)
  var dietDayScreen = document.querySelector(".diet-day-screen");
  if (dietDayScreen) {
    dietDayScreen.addEventListener("click", function (e) {
      var editBtn = e.target.closest(".diet-edit-btn");
      if (editBtn) {
        e.preventDefault();
        var dayName = editBtn.getAttribute("data-day");
        var form = dietDayScreen.querySelector('.diet-edit-form[data-day="' + dayName + '"]');
        if (form) {
          editBtn.hidden = true;
          form.hidden = false;
        }
        return;
      }
      var cancelBtn = e.target.closest(".diet-edit-cancel");
      if (cancelBtn) {
        e.preventDefault();
        var form = cancelBtn.closest(".diet-edit-form");
        var dayName = form.getAttribute("data-day");
        var editBtn = dietDayScreen.querySelector('.diet-edit-btn[data-day="' + dayName + '"]');
        if (editBtn) {
          form.hidden = true;
          editBtn.hidden = false;
        }
        return;
      }
    });

    dietDayScreen.addEventListener("submit", function (e) {
      var form = e.target.closest(".diet-edit-form");
      if (!form || form.tagName !== "FORM") return;
      e.preventDefault();
      var dayName = form.getAttribute("data-day");
      var breakfast = (form.querySelector('[name="breakfast"]') && form.querySelector('[name="breakfast"]').value) || "";
      var lunch = (form.querySelector('[name="lunch"]') && form.querySelector('[name="lunch"]').value) || "";
      var dinner = (form.querySelector('[name="dinner"]') && form.querySelector('[name="dinner"]').value) || "";
      var snacks = (form.querySelector('[name="snacks"]') && form.querySelector('[name="snacks"]').value) || "";
      fetch("/api/diet-plan", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Requested-With": "XMLHttpRequest" },
        body: JSON.stringify({ day_name: dayName, breakfast: breakfast, lunch: lunch, dinner: dinner, snacks: snacks })
      })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (data && data.error) {
            alert(data.error || "Could not save.");
            return;
          }
          var set = function (meal, text) {
            var el = dietDayScreen.querySelector('.diet-meal-content[data-meal="' + meal + '"]');
            if (el) el.textContent = text || "—";
          };
          set("breakfast", breakfast);
          set("lunch", lunch);
          set("dinner", dinner);
          set("snacks", snacks);
          form.hidden = true;
          var editBtn = dietDayScreen.querySelector('.diet-edit-btn[data-day="' + dayName + '"]');
          if (editBtn) editBtn.hidden = false;
        })
        .catch(function () { alert("Could not save diet plan."); });
    });
  }

  // My Exercises page: create + click to play video
  if (window.MY_EXERCISES_PAGE) {
    var form = document.getElementById("create-exercise-form");
    var statusEl = document.getElementById("exercise-create-status");
    var grid = document.getElementById("my-exercises-grid");
    var editModal = document.getElementById("exercise-edit-modal");
    var editForm = document.getElementById("edit-exercise-form");
    var editStatus = document.getElementById("exercise-edit-status");
    var closeEditBtn = document.getElementById("close-ex-edit");

    if (form) {
      form.addEventListener("submit", function (e) {
        e.preventDefault();
        if (statusEl) statusEl.textContent = "Saving…";
        var fd = new FormData(form);
        fetch("/api/my-exercises", { method: "POST", body: fd })
          .then(function (r) { return r.json(); })
          .then(function (data) {
            if (data && data.error) {
              if (statusEl) statusEl.textContent = data.error;
              return;
            }
            if (statusEl) statusEl.textContent = "Added.";
            if (typeof window.location !== "undefined") window.location.reload();
          })
          .catch(function () { if (statusEl) statusEl.textContent = "Failed to save."; });
      });
    }

    if (grid) {
      grid.addEventListener("click", function (e) {
        var delBtn = e.target.closest(".exercise-delete");
        if (delBtn) {
          e.preventDefault();
          var delId = delBtn.getAttribute("data-id");
          if (!delId) return;
          if (!confirm("Delete this exercise?")) return;
          fetch("/api/my-exercises/" + encodeURIComponent(delId), { method: "DELETE" })
            .then(function (r) { return r.json(); })
            .then(function (data) {
              if (data && data.error) { alert(data.error); return; }
              window.location.reload();
            })
            .catch(function () { alert("Failed to delete."); });
          return;
        }

        var editBtn = e.target.closest(".exercise-edit");
        if (editBtn) {
          e.preventDefault();
          var tileForEdit = editBtn.closest(".exercise-tile");
          try {
            var exEdit = exerciseFromTile(tileForEdit);
            if (!exEdit) return;
            document.getElementById("edit-ex-id").value = exEdit.id || "";
            document.getElementById("edit-ex-name").value = exEdit.name || "";
            var mg = (tileForEdit.dataset && tileForEdit.dataset.muscleGroup) ? tileForEdit.dataset.muscleGroup : (exEdit.muscle_group || "");
            document.getElementById("edit-ex-mg").value = (mg || "").toLowerCase();
            document.getElementById("edit-ex-image-url").value = exEdit.image_url || "";
            document.getElementById("edit-ex-video-url").value = exEdit.video_url || "";
            if (editStatus) editStatus.textContent = "";
            if (editModal) editModal.classList.remove("hidden");
          } catch (err) {}
          return;
        }

        var tile = e.target.closest(".exercise-tile");
        if (!tile) return;
        if (e.target.closest(".exercise-edit") || e.target.closest(".exercise-delete")) return;
        try {
          var ex = exerciseFromTile(tile);
          if (!ex) return;
          openImageThenVideo(ex);
        } catch (err) {}
      });
    }

    if (closeEditBtn && editModal) {
      closeEditBtn.addEventListener("click", function () { editModal.classList.add("hidden"); });
      editModal.querySelector(".modal-backdrop").addEventListener("click", function () { editModal.classList.add("hidden"); });
    }

    if (editForm) {
      editForm.addEventListener("submit", function (e) {
        e.preventDefault();
        var id = document.getElementById("edit-ex-id").value;
        if (!id) return;
        if (editStatus) editStatus.textContent = "Saving…";
        var fd = new FormData(editForm);
        fetch("/api/my-exercises/" + encodeURIComponent(id), { method: "PUT", body: fd })
          .then(function (r) { return r.json(); })
          .then(function (data) {
            if (data && data.error) { if (editStatus) editStatus.textContent = data.error; return; }
            if (editStatus) editStatus.textContent = "Saved.";
            window.location.reload();
          })
          .catch(function () { if (editStatus) editStatus.textContent = "Failed to save."; });
      });
    }
  }

  // Schedule day page: click card -> video or image
  if (window.SCHEDULE_DAY_PAGE) {
    var sGrid = document.getElementById("schedule-day-exercises");
    if (sGrid) {
      sGrid.addEventListener("click", function (e) {
        var tile = e.target.closest(".exercise-tile");
        if (!tile) return;
        try {
          var ex = exerciseFromTile(tile);
          if (!ex) return;
          openImageThenVideo(ex);
        } catch (err) {}
      });
    }
  }
})();
