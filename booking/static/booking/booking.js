function mkInput(name, type = 'text') {
  const input = document.createElement('input');
  input.type = type;
  input.name = name;
  input.className = 'bt-field'; // 🔥 WAJIB
  return input;
}

function mkSelect(name, options) {
  const select = document.createElement('select');
  select.name = name;
  select.className = 'bt-field'; // 🔥 WAJIB

  options.forEach(opt => {
    const o = document.createElement('option');
    o.value = opt.value;
    o.textContent = opt.label;
    select.appendChild(o);
  });

  return select;
}

function renderMembers(pax) {
  const container = document.getElementById('members-container');
  container.innerHTML = '';

  for (let i = 0; i < pax; i++) {
    const card = document.createElement('div');
    card.className = 'member-card';

    // Nama
    const nameGroup = document.createElement('div');
    nameGroup.className = 'form-group';
    nameGroup.innerHTML = `<label>Nama</label>`;
    nameGroup.appendChild(mkInput(`name_${i}`));

    // Usia
    const ageGroup = document.createElement('div');
    ageGroup.className = 'form-group';
    ageGroup.innerHTML = `<label>Usia</label>`;
    ageGroup.appendChild(mkInput(`age_${i}`, 'number'));

    // Gender
    const genderGroup = document.createElement('div');
    genderGroup.className = 'form-group';
    genderGroup.innerHTML = `<label>Jenis Kelamin</label>`;
    genderGroup.appendChild(
      mkSelect(`gender_${i}`, [
        { value: 'M', label: 'Laki-laki' },
        { value: 'F', label: 'Perempuan' },
        { value: 'O', label: 'Lainnya' },
      ])
    );

    // Level
    const levelGroup = document.createElement('div');
    levelGroup.className = 'form-group';
    levelGroup.innerHTML = `<label>Level Pendaki</label>`;
    levelGroup.appendChild(
      mkSelect(`level_${i}`, [
        { value: 'beginner', label: 'Pemula' },
        { value: 'intermediate', label: 'Menengah' },
        { value: 'advanced', label: 'Mahir' },
      ])
    );

    card.append(nameGroup, ageGroup, genderGroup, levelGroup);
    container.appendChild(card);
  }
}
