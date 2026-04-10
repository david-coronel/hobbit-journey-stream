# Diseño de Long Gaps: Arcos Narrativos + Day-Patterns

Los 4 long gaps concentran el 86.7% del tiempo de gap del stream. Cada uno necesita una **estructura dramática propia** que evite la monotonía y respete la narrativa de Tolkien.

> Principio: un long gap no es "un día repetido 128 veces". Es una **novela en miniatura** con actos, transiciones y puntos de inflexión.

---

## 1. El Cautiverio — `gap_canon_044_canon_045` (128 días, Mirkwood)

### Arco narrativo: U-curve de esperanza

```
Shock ──► Aislamiento ──► Rutina ──► Primera esperanza ──► Conspiración ──► Escape
```

| Fase | Días | Tensión | Color emocional |
|------|------|---------|-----------------|
| **Acto I: Caída** | 1–7 | Alta, descendente | Miedo, desorientación, silencio forzado |
| **Acto II: Rutina I** | 8–40 | Baja, plana | Monotonía, pequeñas victorias de Bilbo, comida elfica |
| **Acto III: Rutina II** | 41–90 | Muy baja | Vacío, estancamiento, olvido del tiempo |
| **Acto IV: Resurgimiento** | 91–115 | Media, ascendente | Bilbo empieza a moverse, contacto con enanos, plan del barril |
| **Acto V: Clímax** | 116–128 | Alta, explosiva | Tensión de escape, últimos preparativos, noche del barril |

### Day-patterns por fase

#### Acto I (días 1–7): `dungeon_day`
```
Mañana:   Despertar en celda → Ración elfica → Silencio / meditación forzada
Tarde:    Paseo obligado por el patio (si aplica) → Bilbo observa invisible
Noche:    Primeras noches de insomnio → Pesadillas → Vigilia angustiosa
```
Bloques frecuentes: `inner_monologue`, `ambient_pause`, `pair_dialogue` (susurros entre celdas), `accidente_menor` (golpes contra barrotes), `meal_preparation` (ración fría).

#### Acto II–III (días 8–90): `prison_routine_day`
```
Mañana:   Despertar mecánico → Ración → Pausa vacía
Tarde:    Bilbo camina invisible por palacio → Observa rutina de guardias
Noche:    Sueño pesado / algunos enanos juegan a las cartas en silencio
```
Bloques frecuentes: `individual_task`, `ambient_pause`, `group_meal` (comida en silencio), `inner_monologue`, `cultural_ritual` (oración enana a Mahal), `pair_dialogue` (Bilbo contacta a un enano).

Eventos especiales esporádicos (1–2 por semana):
- **Fiesta de los elfos**: música lejana, luz de antorchas, envidia mezclada con repulsión.
- **Cambio de estación**: notar que hace más frío o más cálido.
- **Visita de un elfo importante**: interrupción del silencio, tensión momentánea.
- **Enfermedad de un enano**: tos persistente, preocupación compartida.
- **Bilbo encuentra una llave / una ruta nueva**.

#### Acto IV (días 91–115): `planning_day`
```
Mañana:   Bilbo reporta a Thorin lo que ha visto
Tarde:    Bilbo contacta a más enanos celda por celda
Noche:    Reunión susurrada / elaboración del plan del barril
```
Bloques frecuentes: `pair_dialogue`, `strategic_discussion`, `inner_monologue` (dudas de Bilbo), `comic_relief` (dificultad de explicar el plan), `exploration` (Bilbo mapea).

#### Acto V (días 116–128): `escape_eve_day`
```
Mañana:   Últimos preparativos / nerviosismo
Tarde:    Espera de la noche correcta (clima, guardias, luna)
Noche:    Ejecución del escape (propio del gap, no de la escena canónica)
```
Bloques frecuentes: `strategic_discussion`, `event` (señales acordadas), `inner_monologue`, `ambient_pause` (tensión máxima).

### Eventos de ruptura obligatorios
- **Día 1**: Desarme y separación.
- **Día 3**: Thorin al fondo de la mazmorra.
- **Día 5**: Bilbo descubre que puede moverse libremente.
- **Día 45** (aprox): Fiesta de los elfos más ruidosa del año.
- **Día 100** (aprox): Bilbo consigue contactar a todos los enanos.
- **Día 110**: La idea del barril emerge y se acepta.
- **Día 125**: La noche del escape se fija.

---

## 2. La Espera de Smaug — `gap_canon_064_canon_065` (16 días, Erebor)

### Arco narrativo: Thriller de tensión creciente

```
Alivio ──► Calma tensa ──► Paranoia ──► Catástrofe confirmada
```

| Fase | Días | Tensión | Color emocional |
|------|------|---------|-----------------|
| **Acto I: La salida** | 1 | Muy alta, luego vacío | Terror inicial, silencio ensordecedor |
| **Acto II: Espera** | 2–8 | Media, creciente | Exploración de Erebor, rumores, racionamiento |
| **Acto III: Paranoia** | 9–13 | Alta | Cada sonido es Smaug. Gandalf no está. |
| **Acto IV: Confirmación** | 14–16 | Muy alta | Noticias de Lake-town. Muerte del dragón. |

### Day-patterns por fase

#### Acto I (día 1): `dragon_departure_day`
```
Mañana:   Smaug despierta, vuela en furia
Tarde:    Silencio absoluto en Erebor
Noche:    Ninguno duerme. Vigilia compartida.
```
Bloques: `event`, `ambient_pause`, `group_meal` (sin apetito), `inner_monologue` (Thorin).

#### Acto II–III (días 2–13): `siege_day`
```
Mañana:   Despertar con miedo. Revisar provisiones.
Tarde:    Explorar Erebor con cautela. Contar tesoros. Escuchar.
Noche:    Vigilia. Cada ruido genera alarma.
```
Bloques: `individual_task`, `exploration`, `pair_dialogue`, `ambient_pause`, `night_watch`, `strategic_discussion` ("¿debemos ir a Lake-town?").

Eventos especiales esporádicos:
- **Eco de un rugido lejano** (día 4).
- **Un cuervo trae noticias confusas** (día 7).
- **Discusión seria sobre abandonar la montaña** (día 9).
- **Kili o Fili insisten en salir; Thorin se niega** (día 11).

#### Acto IV (días 14–16): `aftermath_eve_day`
```
Mañana:   Luz roja al sur. Tragedia inminente.
Tarde:    Rumores sólidos de destrucción.
Noche:    Confirmación de la muerte de Smaug. Celebración ambivalente.
```
Bloques: `event`, `pair_dialogue`, `group_meal` (ahora con esperanza), `inner_monologue` (Thorin siente culpa por el oro).

### Eventos de ruptura obligatorios
- **Día 1, madrugada**: Smaug despierta y vuela hacia Lake-town.
- **Día 7**: Un cuervo (no Roäc todavía) trae rumores.
- **Día 14**: Luz de fuego en el horizonte sur.
- **Día 16**: Confirmación de que Smaug ha muerto. La montaña es suya.

---

## 3. Invierno en Rivendell — `gap_canon_093_canon_094` (160 días, The Road East → Rivendell)

### Arco narrativo: Pastoral con melancolía subyacente

```
Viaje final ──► Descanso bendecido ──► Estancamiento invernal ──► Renacimiento
```

| Fase | Días | Tensión | Color emocional |
|------|------|---------|-----------------|
| **Acto I: Último tramo** | 1–10 | Media | Despedida de la Montaña, nostalgia de la aventura |
| **Acto II: Llegada y acogida** | 11–30 | Baja, cálida | Fiestas, música, curación, historias |
| **Acto III: Invierno profundo** | 31–140 | Muy baja | Nieve, lectura, silencio, espera |
| **Acto IV: Deshielo** | 141–160 | Media, esperanzada | Preparativos, despedidas, primer brotes |

### Day-patterns por fase

#### Acto I (días 1–10): `homeward_travel_day`
```
Mañana:   Marcha lenta hacia el oeste
Tarde:    Última visita a Beorn (día 3–4)
Noche:    Campamento bajo estrellas, conversación melancólica
```
Bloques: `travel` patterns (marcha reducida), `group_meal`, `inner_monologue`, `farewell_arrival`, `cultural_ritual` (canto de despedida enano).

#### Acto II (días 11–30): `rivendell_welcome_day`
```
Mañana:   Despertar tarde en habitaciones élficas
Tarde:    Paseo por los jardines, lectura, conversación con Elrond
Noche:    Cena con música, Gandalf cuenta historias del Concilio Blanco
```
Bloques: `wake_and_ritual` (suave, élfico), `individual_task` (Bilbo escribe), `group_meal` (festivo), `pair_dialogue` (Bilbo y Elrond), `cultural_ritual` (canto élfico), `exploration` (jardines de Rivendell).

Eventos especiales esporádicos:
- **Concierto élfico** (día 15).
- **Gandalf revela algo de Dol Guldur** en voz baja (día 20).
- **Fili o Kili reciben atención médica por heridas de batalla** (día 18).
- **Bilbo empieza a escribir su libro** (día 22).

#### Acto III (días 31–140): `rivendell_winter_day`
```
Mañana:   Despertar con nieve en el alféizar
Tarde:    Muy poca actividad. Lectura, conversaciones lentas, juegos de mesa enano-elfo.
Noche:    Cena temprana. Canciones de fuego y hielo.
```
Bloques: `ambient_pause` (nieve), `individual_task`, `group_meal` (pequeña, íntima), `pair_dialogue`, `inner_monologue` (Bilbo extraña y no extraña su antigua vida), `cultural_ritual` (poemas élficos recitados), `comic_relief` (enanos no entienden las costumbres élficas).

Eventos especiales (1 por semana aprox):
- **Cambio de fase lunar** (observación desde los balcones).
- **Visita de un mensajero élfico** con noticias del sur.
- **Thorin habla con Bilbo sobre el oro y la codicia** (día 80 aprox, momento clave de reconciliación).
- **Un enano enferma de fiebre y es curado por Elrond**.
- **Noche de historias: Balin cuenta Moria**.
- **Bilbo termina un capítulo de su libro**.

#### Acto IV (días 141–160): `rivendell_farewell_day`
```
Mañana:   Deshielo visible. Preparativos de viaje.
Tarde:    Últimos paseos, últimas conversaciones.
Noche:    Cena de despedida con Elrond. Promesas de regreso.
```
Bloques: `exploration`, `pair_dialogue`, `farewell_arrival`, `cultural_ritual` (intercambio de regalos), `group_meal` (emotiva), `strategic_discussion` (ruta final).

### Eventos de ruptura obligatorios
- **Día 4**: Última noche en casa de Beorn.
- **Día 10**: Llegada a Rivendell.
- **Día 15**: Primer concierto/fiesta de bienvenida.
- **Día 80** (aprox): Thorin y Bilbo conversan sobre codicia y perdón.
- **Día 141**: Primer día de deshielo visible.
- **Día 155**: Última gran cena con Elrond.
- **Día 160**: Partida hacia el Oeste.

---

## 4. El Viaje Final a Casa — `gap_canon_094_canon_095` (52 días, The Shire)

### Arco narrativo: Road movie de clausura

```
Melancolía de despedida ──► Nostalgia del camino ──► Aceleración emocional ──► Llegada
```

| Fase | Días | Tensión | Color emocional |
|------|------|---------|-----------------|
| **Acto I: De Rivendell al Vado** | 1–20 | Media | Lluvia, verde, recuerdos |
| **Acto II: Tierras Salvajes otra vez** | 21–40 | Baja | Camino conocido, conversaciones sobre el futuro |
| **Acto III: Fronteras de la Comarca** | 41–48 | Media-alta | Calor de verano, emoción contenida |
| **Acto IV: Llegada** | 49–52 | Alta | Hobbiton, la subasta, la casa vacía |

### Day-patterns por fase

#### Acto I (días 1–20): `wet_road_day`
```
Mañana:   Marcha bajo lluvia fina o cielo gris
Tarde:    Cruce de ríos, recuerdo de lugares antiguos
Noche:    Campamento en colinas verdes
```
Bloques: `travel` reducido, `group_meal`, `inner_monologue` (Bilbo), `pair_dialogue` (Bilbo y Gandalf), `exploration` (cruce de vado), `cultural_ritual` (canto enano de despedida).

Eventos especiales:
- **Recuperación del oro enterrado en los Trollshaws** (día 8).
- **Lluvia torrencial que los obliga a refugiarse** (día 12).
- **Encuentro con un hobbit errante que no reconoce a Bilbo** (día 15).

#### Acto II (días 21–40): `familiar_road_day`
```
Mañana:   Camino más suave, colinas redondeadas
Tarde:    Conversaciones sobre qué hará cada uno al llegar
Noche:    Fuegos de campamento más alegres
```
Bloques: `pair_dialogue`, `group_meal`, `inner_monologue` (Thorin ya no está, compañía más pequeña), `comic_relief`, `cultural_ritual` (dwarven dice games).

Eventos especiales:
- **Última gran discusión sobre el reparto del tesoro** (día 25).
- **Gandalf anuncia que se separará pronto** (día 30).
- **Bilbo regala algo de su tesoro a los enanos que lo acompañan** (día 35).

#### Acto III (días 41–48): `shire_border_day`
```
Mañana:   Primeros campos de la Comarca
Tarde:    Aromas familiares, clima cálido
Noche:    Últimas noches de campamento
```
Bloques: `ambient_pause` (verano), `exploration` (reconocer lugares), `pair_dialogue`, `group_meal`, `farewell_arrival` (enanos que se despiden antes).

Eventos especiales:
- **Primer vistazo de la Colina desde lejos** (día 43).
- **Despedida de los últimos enanos que no van a Hobbiton** (día 45).
- **Gandalf y Bilbo caminan solos los últimos tramos** (día 46–48).

#### Acto IV (días 49–52): `homecoming_day`
```
Mañana:   Entrada a Hobbiton
Tarde:    La subasta en curso. Sorpresa y confusión.
Noche:     
```
Bloques: `event`, `pair_dialogue` (Bilbo y los Sackville-Baggins), `inner_monologue` (Bilbo en su casa vacía), `comic_relief` (confusión sobre su supuesta muerte), `ambient_pause` (paz final).

### Eventos de ruptura obligatorios
- **Día 8**: Recuperan el oro de los Trollshaws.
- **Día 30**: Gandalf anuncia su despedida.
- **Día 43**: Primera vista de la Colina.
- **Día 49**: Llegada a Hobbiton.
- **Día 50**: Bilbo descubre la subasta.
- **Día 52**: Entrada a Bolsón Cerrado. Fin del viaje.

---

## Estructura de Datos Propuesta

Cada long gap debería generar algo así en `gap_plans.json`:

```json
{
  "type": "subplot",
  "title": "The Long Captivity",
  "duration_hours": 3079.5,
  "children": [
    {
      "type": "phase",
      "title": "Act I: The Fall",
      "duration_hours": 168,
      "phase_id": "captivity_fall",
      "day_pattern": "dungeon_day",
      "days": 7,
      "mood": "fear",
      "special_events": ["Disarming", "Thorin to the depths", "Bilbo discovers freedom"]
    },
    {
      "type": "phase",
      "title": "Act II-III: The Long Routine",
      "duration_hours": 1992,
      "phase_id": "captivity_routine",
      "day_pattern": "prison_routine_day",
      "days": 83,
      "mood": "monotony",
      "special_events": ["Elf feast distant", "Season change", "Bilbo contacts all dwarves"]
    },
    {
      "type": "phase",
      "title": "Act IV: The Plan",
      "duration_hours": 600,
      "phase_id": "captivity_planning",
      "day_pattern": "planning_day",
      "days": 25,
      "mood": "rising_hope",
      "special_events": ["Barrel idea emerges"]
    },
    {
      "type": "phase",
      "title": "Act V: Escape Eve",
      "duration_hours": 312,
      "phase_id": "captivity_escape",
      "day_pattern": "escape_eve_day",
      "days": 13,
      "mood": "thriller",
      "special_events": ["The right night", "The escape"]
    }
  ]
}
```

El motor procedural, al llegar al día 67 del cautiverio, ejecutaría:
1. `phase_id = captivity_routine` (día 67 está en el rango de días 8–90)
2. `day_pattern = prison_routine_day`
3. Elige bloques de ese day-pattern según hora del día y estado del mundo.
4. Aplica el `mood = monotony` a los prompts generativos.
5. Si el día coincide con un `special_event`, reemplaza un bloque normal por el evento especial.

---

## Pregunta para decidir

¿Querés que **codifique estas 4 estructuras de fases** directamente en `gap_planner.py` para los long gaps? O preferís ajustar primero algunos números de días por fase o los eventos especiales.
