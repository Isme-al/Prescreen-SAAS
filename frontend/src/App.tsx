import { Outlet, NavLink } from "react-router-dom";

export default function App() {
  return (
    <>
      <header className="app-header">
        <div className="container">
          <h1>Prescreener</h1>
          <nav>
            <NavLink to="/" className={({ isActive }) => isActive ? "active" : ""} end>
              Screen
            </NavLink>
            <NavLink to="/protocols" className={({ isActive }) => isActive ? "active" : ""}>
              Protocols
            </NavLink>
          </nav>
        </div>
      </header>
      <main className="container page">
        <Outlet />
      </main>
    </>
  );
}
