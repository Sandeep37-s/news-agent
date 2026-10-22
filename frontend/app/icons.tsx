type IconName = 'overview'|'india'|'cinema'|'globe'|'prompt'|'activity'|'settings'|'search'|'arrow'|'refresh';

const paths: Record<IconName,string> = {
  overview:'M3 3h7v7H3z M14 3h7v11h-7z M3 14h7v7H3z M14 18h7v3h-7z',
  india:'M12 21s7-5.5 7-12A7 7 0 0 0 5 9c0 6.5 7 12 7 12Z M9.5 9a2.5 2.5 0 1 0 5 0 2.5 2.5 0 0 0-5 0',
  cinema:'M3 8h18v13H3z M3 8V3h18v5 M8 3l-3 5 M15 3l-3 5 M21 3l-3 5 M10 12l5 3-5 3z',
  globe:'M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0 M3 12h18 M12 3c5 5 5 13 0 18-5-5-5-13 0-18',
  prompt:'M14 3H5v18h14V8z M14 3v5h5 M8 12h8 M8 16h5',
  activity:'M3 12h4l3-8 4 16 3-8h4',
  settings:'m9 3-.6 2.4-2.2 1.3L3.8 6 1.8 9.5 3.6 11v2l-1.8 1.5 2 3.5 2.4-.7 2.2 1.3L9 21h4l.6-2.4 2.2-1.3 2.4.7 2-3.5-1.8-1.5v-2l1.8-1.5-2-3.5-2.4.7-2.2-1.3L13 3z M8 12a3 3 0 1 0 6 0 3 3 0 0 0-6 0',
  search:'M20 20l-5-5 M17 10a7 7 0 1 1-14 0 7 7 0 0 1 14 0',
  arrow:'M5 12h14 M13 6l6 6-6 6',
  refresh:'M20 7v5h-5 M20 12a8 8 0 1 0-2 5 M20 7a8 8 0 0 0-13-2',
};

export function Icon({name,className=''}:{name:IconName;className?:string}){
  return <svg className={'icon '+className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={paths[name]}/></svg>;
}

export const navigationIcons: IconName[] = ['overview','india','cinema','globe','prompt','activity','settings'];

export function StudioArtwork(){
  return <svg className="studio-artwork" viewBox="0 0 340 260" fill="none" aria-hidden="true">
    <circle cx="194" cy="130" r="103" stroke="#788489" strokeOpacity=".25"/>
    <circle cx="194" cy="130" r="78" stroke="#788489" strokeOpacity=".25"/>
    <path d="M194 12v236M76 130h236" stroke="#788489" strokeOpacity=".16"/>
    <g transform="rotate(-9 170 130)"><rect x="73" y="39" width="164" height="190" rx="13" fill="#121D25" stroke="#5E6A71"/>
      <rect x="91" y="59" width="66" height="6" rx="3" fill="#D5AA87"/><path d="M91 84h120M91 96h89" stroke="#EAE4DA" strokeWidth="8"/>
      <rect x="91" y="116" width="128" height="60" rx="5" fill="#293943"/>
      <path d="m104 158 23-21 20 12 26-22 30 15" stroke="#D5AA87" strokeWidth="3"/>
      <path d="M91 194h128M91 205h79" stroke="#65747D" strokeWidth="4"/>
    </g>
    <g transform="rotate(8 248 159)"><rect x="189" y="116" width="119" height="96" rx="10" fill="#D9AD89"/>
      <circle cx="248" cy="162" r="23" stroke="#17242D" strokeOpacity=".25"/><path d="m241 151 19 11-19 11z" fill="#17242D"/>
    </g>
    <circle cx="270" cy="62" r="21" fill="#344840"/><path d="m260 62 7 7 13-14" stroke="#BFD6B9" strokeWidth="2"/>
    <circle cx="53" cy="159" r="4" fill="#D9AD89"/><circle cx="290" cy="235" r="3" fill="#788489"/>
  </svg>;
}
