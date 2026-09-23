import { NavLink, Outlet } from 'react-router-dom'

const navItems = [
  { to: '/', label: '首页概览' },
  { to: '/jobs', label: '岗位查询' },
  { to: '/dashboard', label: '数据分析' },
]

export default function Layout() {
  return (
    <div className="min-h-full flex flex-col">
      <header className="bg-brand-500 text-white shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-2">
              <span className="text-2xl">📊</span>
              <span className="font-bold text-lg tracking-wide">济宁热门工作岗位分析</span>
            </div>
            <nav className="flex gap-1 sm:gap-2">
              {navItems.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === '/'}
                  className={({ isActive }) =>
                    `px-3 sm:px-4 py-2 rounded-lg text-sm font-medium transition ${
                      isActive
                        ? 'bg-white/20 text-white'
                        : 'text-white/80 hover:bg-white/10 hover:text-white'
                    }`
                  }
                >
                  {item.label}
                </NavLink>
              ))}
            </nav>
          </div>
        </div>
      </header>
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <Outlet />
      </main>
      <footer className="border-t border-slate-200 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 text-xs text-slate-400 text-center space-y-1">
          <p>
            数据来源：济宁市人社局《标志性产业链重点人才需求蓝皮书（2026版）》、济宁市属事业单位公开招聘公告、汶上县招聘公告、济宁直聘网等公开渠道 ·
            采集日期 2026-09-23 ·
            仅供分析参考，不作为求职决策唯一依据
          </p>
          <p className="text-slate-300">
            本站数据来源于公开的《济宁蓝皮书》及招聘公告，仅作行业分析参考，不提供直接投递服务。求职请认准官方招聘平台，谨防诈骗。
          </p>
        </div>
      </footer>
    </div>
  )
}
