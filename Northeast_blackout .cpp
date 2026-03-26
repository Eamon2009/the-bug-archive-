/**
 * =============================================================================
 * BUG ARCHIVE — Entry #7
 * Incident  : Northeast Blackout — 55 Million Without Power
 * Date      : August 14, 2003
 * Language  : C++ (GE Energy's XA/21 Energy Management System)
 *             XA/21 was a C++ application running on HP-UX Unix servers.
 * Root Cause: A race condition in the alarm management subsystem caused
 *             the alarm server thread to become deadlocked. The system
 *             continued running but stopped delivering any alerts.
 *             Operators saw a silent dashboard for 90 minutes while
 *             three transmission lines failed and a cascade began.
 * Loss      : ~$6 billion | Lives Lost: ~100
 * =============================================================================
 *
 * The XA/21 system used a producer-consumer alarm queue shared between
 * the grid monitoring thread (producer) and the alarm display thread
 * (consumer). A mutex deadlock under high alarm load caused the consumer
 * thread to freeze. No watchdog detected the freeze. The dashboard
 * continued showing the last known state — normal — for 90 minutes.
 *
 * =============================================================================
 */

#include <iostream>
#include <thread>
#include <mutex>
#include <queue>
#include <string>
#include <chrono>
#include <atomic>
#include <iomanip>
#include <functional>

using namespace std::chrono_literals;

// ── Alarm severity levels ─────────────────────────────────────────────────────
enum class Severity
{
       INFO,
       WARNING,
       CRITICAL,
       EMERGENCY
};

std::string severity_str(Severity s)
{
       switch (s)
       {
       case Severity::INFO:
              return "INFO     ";
       case Severity::WARNING:
              return "WARNING  ";
       case Severity::CRITICAL:
              return "CRITICAL ";
       case Severity::EMERGENCY:
              return "EMERGENCY";
       }
       return "UNKNOWN";
}

struct GridAlarm
{
       std::string message;
       Severity severity;
};

// Grid events — the real sequence from the August 14, 2003 cascade
static const GridAlarm GRID_EVENTS[] = {
    {"Stuart-Atlanta 345kV line trips offline", Severity::WARNING},
    {"Voltage sag detected in NE Ohio", Severity::WARNING},
    {"Harding-Chamberlin 345kV line trips offline", Severity::CRITICAL},
    {"Toledo generating unit 4 offline — load imbalance growing", Severity::CRITICAL},
    {"Hanna-Juniper 345kV line trips offline", Severity::CRITICAL},
    {"CASCADE: Ohio grid separating from eastern interconnect", Severity::EMERGENCY},
    {"CASCADE: Michigan/Pennsylvania grids tripping", Severity::EMERGENCY},
    {"CASCADE: New York and Ontario grids tripping", Severity::EMERGENCY},
    {"BLACKOUT: 55 million customers without power", Severity::EMERGENCY},
};
static const int N_EVENTS = sizeof(GRID_EVENTS) / sizeof(GRID_EVENTS[0]);

// =============================================================================
//     BUGGY XA/21 ALARM MANAGER
//     Classic C++ deadlock pattern: two mutexes acquired in inconsistent order.
//     Under load, the alarm thread deadlocks silently.
//     No watchdog. No timeout. Operators see silence.
// =============================================================================

class BuggyAlarmManager
{
public:
       std::string name = "XA/21 Alarm Manager (BUGGY)";

       void raise(const GridAlarm &alarm)
       {
              std::lock_guard<std::mutex> lock(queue_mutex_);
              alarm_queue_.push(alarm);
       }

       //  Alarm consumer thread — acquires queue_mutex THEN display_mutex.
       //    If another codepath acquires display_mutex THEN queue_mutex,
       //    deadlock results. Thread silently hangs. No one is notified.
       void run_alarm_thread()
       {
              int processed = 0;
              while (running_)
              {
                     GridAlarm alarm;
                     bool got_alarm = false;

                     {
                            std::lock_guard<std::mutex> lock(queue_mutex_); // lock A
                            if (!alarm_queue_.empty())
                            {
                                   alarm = alarm_queue_.front();
                                   alarm_queue_.pop();
                                   got_alarm = true;
                            }
                     }

                     if (got_alarm)
                     {
                            processed++;
                            // Simulate deadlock under load at alarm #5
                            // Real XA/21: race condition caused thread hang after ~90 mins
                            if (processed == 5)
                            {
                                   std::cerr << "  [AlarmThread] Race condition triggered — "
                                                "thread deadlocked. No more alarms delivered.\n";
                                   // Thread hangs here. Silently. Forever.
                                   // Operators see a quiet dashboard.
                                   while (running_)
                                          std::this_thread::sleep_for(100ms);
                                   return;
                            }

                            // No heartbeat updated — watchdog can't detect this hang
                            std::cout << "  [ALARM] " << severity_str(alarm.severity)
                                      << "  " << alarm.message << "\n";
                            delivered_count_++;
                     }
                     std::this_thread::sleep_for(30ms);
              }
       }

       void start()
       {
              running_ = true;
              worker_ = std::thread(&BuggyAlarmManager::run_alarm_thread, this);
       }

       void stop()
       {
              running_ = false;
              if (worker_.joinable())
                     worker_.join();
       }

       int delivered() const { return delivered_count_; }

private:
       std::queue<GridAlarm> alarm_queue_;
       std::mutex queue_mutex_;
       std::mutex display_mutex_; // ← second mutex (deadlock partner)
       std::atomic<bool> running_{false};
       std::atomic<int> delivered_count_{0};
       std::thread worker_;
};

// =============================================================================
//   FIXED ALARM MANAGER
//     Single mutex. Heartbeat updated every loop iteration.
//     Watchdog thread monitors heartbeat — raises EMERGENCY if silent > 1s.
//     Inspired by post-incident remediation practices.
// =============================================================================

class FixedAlarmManager
{
public:
       std::string name = "XA/21 Alarm Manager (FIXED)";

       void raise(const GridAlarm &alarm)
       {
              std::lock_guard<std::mutex> lock(mutex_);
              alarm_queue_.push(alarm);
       }

       //  Single mutex. No lock ordering problem. Heartbeat on every iteration.
       void run_alarm_thread()
       {
              int processed = 0;
              while (running_)
              {
                     last_heartbeat_ = std::chrono::steady_clock::now(); //  heartbeat

                     GridAlarm alarm;
                     bool got_alarm = false;
                     {
                            std::lock_guard<std::mutex> lock(mutex_);
                            if (!alarm_queue_.empty())
                            {
                                   alarm = alarm_queue_.front();
                                   alarm_queue_.pop();
                                   got_alarm = true;
                            }
                     }

                     if (got_alarm)
                     {
                            processed++;
                            // No special case — all alarms delivered cleanly
                            std::cout << "  [ALARM] " << severity_str(alarm.severity)
                                      << "  " << alarm.message << "\n";
                            delivered_count_++;
                     }
                     std::this_thread::sleep_for(30ms);
              }
       }

       //  Watchdog: if alarm thread goes silent > 1 second, raise EMERGENCY
       void run_watchdog()
       {
              std::this_thread::sleep_for(200ms); // let alarm thread start
              while (running_)
              {
                     auto now = std::chrono::steady_clock::now();
                     auto gap_ms = std::chrono::duration_cast<std::chrono::milliseconds>(
                                       now - last_heartbeat_.load())
                                       .count();

                     if (gap_ms > 1000)
                     {
                            std::cout << "\n  [WATCHDOG] 🚨 ALARM THREAD UNRESPONSIVE ("
                                      << gap_ms << "ms since last heartbeat)\n";
                            std::cout << "  [WATCHDOG] EMERGENCY: Dashboard may show stale data.\n";
                            std::cout << "  [WATCHDOG] OPERATORS: Verify grid status manually NOW.\n\n";
                            running_ = false;
                            return;
                     }
                     std::this_thread::sleep_for(100ms);
              }
       }

       void start()
       {
              running_ = true;
              last_heartbeat_ = std::chrono::steady_clock::now();
              worker_ = std::thread(&FixedAlarmManager::run_alarm_thread, this);
              watchdog_thread_ = std::thread(&FixedAlarmManager::run_watchdog, this);
       }

       void stop()
       {
              running_ = false;
              if (worker_.joinable())
                     worker_.join();
              if (watchdog_thread_.joinable())
                     watchdog_thread_.join();
       }

       int delivered() const { return delivered_count_; }

private:
       std::queue<GridAlarm> alarm_queue_;
       std::mutex mutex_; //  single mutex
       std::atomic<bool> running_{false};
       std::atomic<int> delivered_count_{0};
       std::atomic<std::chrono::steady_clock::time_point>
           last_heartbeat_;
       std::thread worker_;
       std::thread watchdog_thread_;
};

// =============================================================================
// SIMULATION RUNNER
// =============================================================================

template <typename Manager>
void simulate(Manager &mgr)
{
       std::cout << "\n"
                 << std::string(62, '=') << "\n";
       std::cout << "  " << mgr.name << "\n";
       std::cout << std::string(62, '=') << "\n\n";

       mgr.start();

       for (int i = 0; i < N_EVENTS; i++)
       {
              mgr.raise(GRID_EVENTS[i]);
              std::this_thread::sleep_for(120ms);
       }

       std::this_thread::sleep_for(800ms);
       mgr.stop();

       int missed_critical = 0;
       for (auto &e : GRID_EVENTS)
       {
              if (e.severity >= Severity::CRITICAL)
                     missed_critical++;
       }
       // Rough: if delivered < total, some critical events likely missed
       int total_critical = missed_critical;
       int delivered_critical = std::min(mgr.delivered(),
                                         (int)(N_EVENTS));

       std::cout << "\n  Events generated : " << N_EVENTS << "\n";
       std::cout << "  Events delivered : " << mgr.delivered() << "\n";

       if (mgr.delivered() < N_EVENTS)
       {
              std::cout << "\n   OPERATORS WERE BLIND\n";
              std::cout << "     " << (N_EVENTS - mgr.delivered())
                        << " alarms never reached the control room.\n";
              std::cout << "     Grid collapsed while dashboard showed 'normal'.\n\n";
       }
       else
       {
              std::cout << "\n   All alarms delivered. Operators informed.\n\n";
       }
}

int main()
{
       std::cout << "\nNORTHEAST BLACKOUT 2003 — C++ Alarm System Reconstruction\n";

       {
              BuggyAlarmManager buggy;
              simulate(buggy);
       }
       {
              FixedAlarmManager fixed;
              simulate(fixed);
       }

       std::cout << std::string(62, '=') << "\n";
       std::cout << "  LESSON\n";
       std::cout << std::string(62, '=') << "\n";
       std::cout << R"(
  The XA/21 alarm thread hung silently for 90 minutes.
  The dashboard showed green. The grid was collapsing.
  Operators made no intervention because they saw no problem.

  In C++, threads die without notifying anyone by default.
  An uncaught exception, a deadlock, a segfault — the thread
  simply stops. The system continues. Operators see silence.

  → Every critical thread must publish a heartbeat.
  → A watchdog must monitor that heartbeat and alert loudly
    if it goes silent. Silence is a failure mode, not safety.
  → Use a single mutex where possible. Multiple mutexes
    acquired in inconsistent orders are deadlock traps.
  → Use std::lock() or std::scoped_lock for multi-mutex code.
  → Test your alarm system by killing it deliberately.
    If you can't observe its failure, you cannot trust it.
)" << "\n";

       return 0;
}

/*
 * =============================================================================
 * COMPILE:
 *   g++ -std=c++17 -pthread -o blackout northeast_blackout_cpp.cpp
 * RUN:
 *   ./blackout
 * =============================================================================
 */