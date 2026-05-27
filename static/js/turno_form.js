document.addEventListener("DOMContentLoaded", function () {

  const selectSala       = document.getElementById("id_sala");
  const inputCupo        = document.getElementById("id_cupo");
  const textoMaximo      = document.getElementById("capacidad-dinamica");
  const selectActividad  = document.getElementById("id_actividad");
  const selectProfesor   = document.getElementById("id_profesor");
  const inputFecha       = document.getElementById("id_fecha");
  const inputHora        = document.getElementById("id_hora_inicio");
  const btnSubmit        = document.getElementById("id_crear_clase").querySelector("button[type='submit']");

  const todasLasOpciones = Array.from(selectProfesor.options);

  const hoy = new Date();
  hoy.setHours(0, 0, 0, 0);

  // ── Clases de estado visual ────────────────────────────────────────────────
/**"bg-gray-50 border border-gray-300 text-gray-900 text-sm "
                    "rounded-lg focus:ring-primary-600 focus:border-primary-600 "
                    "block w-full p-2.5"*/
  const CLASES_BLOQUEADO  = ["bg-gray-900"];
  const CLASES_HABILITADO = ["bg-gray-50"];

  function bloquearCampo(campo) {
    campo.setAttribute("disabled", "disabled");
    campo.classList.add("bg-gray-900");
    campo.classList.remove("bg-gray-50");
  }

  function habilitarCampo(campo) {
    campo.removeAttribute("disabled");
    campo.classList.remove("bg-gray-900");
    campo.classList.add("bg-gray-50");
  }

  // ── Helpers de error ───────────────────────────────────────────────────────

  function mostrarError(campo, mensaje) {
    limpiarError(campo);
    const p = document.createElement("p");
    p.className = "mt-1.5 text-xs text-red-600 flex items-center gap-1 js-error";
    p.innerHTML = `
      <svg class="w-3.5 h-3.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
        <path fill-rule="evenodd"
          d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
          clip-rule="evenodd"/>
      </svg>
      ${mensaje}`;
    campo.closest("div").appendChild(p);
    campo.classList.add("border-red-400");
  }

  function limpiarError(campo) {
    const contenedor = campo.closest("div");
    contenedor.querySelectorAll(".js-error").forEach(el => el.remove());
    campo.classList.remove("border-red-400");
  }

  // ── Validadores individuales ───────────────────────────────────────────────

  function validarFecha() {
    if (!inputFecha.value) {
      mostrarError(inputFecha, "La fecha es obligatoria.");
      return false;
    }
    const fechaIngresada = new Date(inputFecha.value + "T00:00:00");
    if (fechaIngresada < hoy) {
      mostrarError(inputFecha, "La fecha no puede ser en el pasado.");
      return false;
    }
    limpiarError(inputFecha);
    return true;
  }

  function validarHora() {
    if (!inputHora.value) {
      mostrarError(inputHora, "La hora es obligatoria.");
      return false;
    }
    const [hh, mm] = inputHora.value.split(":").map(Number);
    if (mm !== 0) {
      mostrarError(inputHora, "La hora debe ser en punto (ej: 08:00, 09:00).");
      return false;
    }
    if (hh < 8 || hh > 20) {
      mostrarError(inputHora, "La hora debe estar entre las 08:00 y las 20:00 hs.");
      return false;
    }
    limpiarError(inputHora);
    return true;
  }

  function validarActividad() {
    if (!selectActividad.value) {
      mostrarError(selectActividad, "Seleccioná una actividad.");
      return false;
    }
    limpiarError(selectActividad);
    return true;
  }

  function validarProfesor() {
    if (selectActividad.value && !selectProfesor.value) {
      mostrarError(selectProfesor, "Seleccioná un profesor para la actividad elegida.");
      return false;
    }
    limpiarError(selectProfesor);
    return true;
  }

  function validarSala() {
    if (!selectSala.value) {
      mostrarError(selectSala, "Seleccioná una sala.");
      return false;
    }
    limpiarError(selectSala);
    return true;
  }

  function validarCupo() {
    if (selectSala.value && !inputCupo.value) {
      mostrarError(inputCupo, "Ingresá el cupo.");
      return false;
    }
    const max = parseInt(inputCupo.getAttribute("max"), 10);
    const val = parseInt(inputCupo.value, 10);
    if (val < 1) {
      mostrarError(inputCupo, "El cupo debe ser al menos 1.");
      return false;
    }
    if (max && val > max) {
      mostrarError(inputCupo, `El cupo no puede superar la capacidad de la sala (${max}).`);
      return false;
    }
    limpiarError(inputCupo);
    return true;
  }

  // ── Estado del botón ───────────────────────────────────────────────────────

  function actualizarBoton() {
    const todoCompleto =
      inputFecha.value &&
      inputHora.value &&
      selectActividad.value &&
      selectProfesor.value &&
      selectSala.value &&
      inputCupo.value;

    if (todoCompleto) {
      btnSubmit.removeAttribute("disabled");
      btnSubmit.classList.remove("opacity-50", "cursor-not-allowed");
    } else {
      btnSubmit.setAttribute("disabled", "disabled");
      btnSubmit.classList.add("opacity-50", "cursor-not-allowed");
    }
  }

  // ── Sala → Cupo ────────────────────────────────────────────────────────────

  function controlarCupo() {
    const opcion = selectSala.options[selectSala.selectedIndex];
    if (opcion && opcion.value !== "") {
      habilitarCampo(inputCupo);
      const max = opcion.getAttribute("data-capacidad");
      if (max) {
        inputCupo.setAttribute("max", max);
        if (textoMaximo) textoMaximo.textContent = max;
      }
    } else {
      bloquearCampo(inputCupo);
      inputCupo.value = "";
      inputCupo.removeAttribute("max");
      if (textoMaximo) textoMaximo.textContent = "—";
    }
  }

  // ── Actividad → Profesor ───────────────────────────────────────────────────

  function crearOpcionVacia() {
    const op = document.createElement("option");
    op.value = "";
    op.textContent = "---------";
    return op;
  }

 function controlarProfesores() {
  const actividadElegida = selectActividad.value;
  
  // 1. Limpiar el contenido actual
  selectProfesor.innerHTML = "";

  if (actividadElegida === "") {
    selectProfesor.appendChild(crearOpcionVacia());
    bloquearCampo(selectProfesor); // <-- Bloquear al final de armar el DOM
    return;
  }

  // 2. Insertar la opción por defecto
  selectProfesor.appendChild(crearOpcionVacia());

  let hayCoincidencias = false;
  todasLasOpciones.forEach(function (opcion) {
    if (opcion.value === "") return;
    if (opcion.getAttribute("data-especialidad") === actividadElegida) {
      selectProfesor.appendChild(opcion.cloneNode(true));
      hayCoincidencias = true;
    }
  });

  if (!hayCoincidencias) {
    const aviso = document.createElement("option");
    aviso.value = "";
    aviso.disabled = true;
    aviso.textContent = "No hay profesores para esta actividad";
    selectProfesor.appendChild(aviso);
  }

  // 3. HABILITAR EL CAMPO AL FINAL 
  // Ejecutarlo al final garantiza que las clases CSS se apliquen sobre el DOM ya renderizado
  habilitarCampo(selectProfesor); 
}

  // ── Listeners ──────────────────────────────────────────────────────────────

  inputFecha.addEventListener("blur",   () => { validarFecha();   actualizarBoton(); });
  inputFecha.addEventListener("change", () => { validarFecha();   actualizarBoton(); });

  inputHora.addEventListener("blur",    () => { validarHora();    actualizarBoton(); });
  inputHora.addEventListener("change",  () => { validarHora();    actualizarBoton(); });

  selectActividad.addEventListener("change", () => {
    limpiarError(selectActividad);
    controlarProfesores();
    limpiarError(selectProfesor);
    validarActividad();
    actualizarBoton();
  });

  selectProfesor.addEventListener("change", () => { validarProfesor(); actualizarBoton(); });

  selectSala.addEventListener("change", () => {
    controlarCupo();
    limpiarError(selectSala);
    limpiarError(inputCupo);
    validarSala();
    actualizarBoton();
  });

  inputCupo.addEventListener("blur",  () => { validarCupo(); actualizarBoton(); });
  inputCupo.addEventListener("input", () => { validarCupo(); actualizarBoton(); });

  // ── Init ───────────────────────────────────────────────────────────────────

  controlarCupo();
  controlarProfesores();
  actualizarBoton();
});