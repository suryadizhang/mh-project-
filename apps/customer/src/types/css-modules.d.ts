// CSS Module declarations for TypeScript
declare module '*.css' {
  const styles: { [className: string]: string };
  export default styles;
}

declare module 'react-datepicker/dist/react-datepicker.css' {
  const styles: string;
  export default styles;
}

declare module './datepicker.css' {
  const styles: { [className: string]: string };
  export default styles;
}
