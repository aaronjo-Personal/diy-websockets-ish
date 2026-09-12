import "./style.css";
import { trackMouse } from "./mousehelper";

document.body.textContent = "X: 0, Y: 0";
trackMouse(({ x, y }) => {
  document.body.textContent = `X: ${x.toFixed(3)}, Y: ${y.toFixed(3)}`;
});
