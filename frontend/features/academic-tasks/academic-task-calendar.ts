// File: /frontend/features/academic-tasks/academic-task-calendar.ts
// Purpose: Provides local-date helpers used by the Academic Tasks
// weekly and monthly calendar views.

import type {
  AcademicTaskResponse,
} from "./types";

export function startOfMonday(
  value: Date,
): Date {
  const result =
    new Date(
      value,
    );

  result.setHours(
    0,
    0,
    0,
    0,
  );

  const weekday =
    result.getDay();

  const daysSinceMonday =
    (
      weekday +
      6
    ) %
    7;

  result.setDate(
    result.getDate() -
      daysSinceMonday,
  );

  return result;
}

export function startOfMonth(
  value: Date,
): Date {
  const result =
    new Date(
      value,
    );

  result.setHours(
    0,
    0,
    0,
    0,
  );

  result.setDate(
    1,
  );

  return result;
}

export function addDays(
  value: Date,
  amount: number,
): Date {
  const result =
    new Date(
      value,
    );

  result.setDate(
    result.getDate() +
      amount,
  );

  return result;
}

export function addMonths(
  value: Date,
  amount: number,
): Date {
  const result =
    new Date(
      value,
    );

  const originalDay =
    result.getDate();

  /*
   * Move to day one first so dates such as
   * January 31 do not skip February.
   */
  result.setDate(
    1,
  );

  result.setMonth(
    result.getMonth() +
      amount,
  );

  const lastDayOfTargetMonth =
    new Date(
      result.getFullYear(),
      result.getMonth() +
        1,
      0,
    ).getDate();

  result.setDate(
    Math.min(
      originalDay,
      lastDayOfTargetMonth,
    ),
  );

  return result;
}

export function localDateKey(
  value: Date,
): string {
  const year =
    value.getFullYear();

  const month =
    String(
      value.getMonth() +
        1,
    ).padStart(
      2,
      "0",
    );

  const day =
    String(
      value.getDate(),
    ).padStart(
      2,
      "0",
    );

  return [
    year,
    month,
    day,
  ].join(
    "-",
  );
}

export function getWeekDays(
  weekAnchor: Date,
): Date[] {
  const monday =
    startOfMonday(
      weekAnchor,
    );

  return Array.from(
    {
      length:
        7,
    },
    (
      _,
      index,
    ) =>
      addDays(
        monday,
        index,
      ),
  );
}

export function getMonthGridDays(
  monthAnchor: Date,
): Date[] {
  const firstDay =
    startOfMonth(
      monthAnchor,
    );

  const gridStart =
    startOfMonday(
      firstDay,
    );

  /*
   * Always use six complete weeks.
   * This keeps the month layout stable
   * while navigating between months.
   */
  return Array.from(
    {
      length:
        42,
    },
    (
      _,
      index,
    ) =>
      addDays(
        gridStart,
        index,
      ),
  );
}

export function isSameMonth(
  first: Date,
  second: Date,
): boolean {
  return (
    first.getFullYear() ===
      second.getFullYear() &&
    first.getMonth() ===
      second.getMonth()
  );
}

export function groupAcademicTasksByDeadlineDay(
  tasks: AcademicTaskResponse[],
): Map<
  string,
  AcademicTaskResponse[]
> {
  const result =
    new Map<
      string,
      AcademicTaskResponse[]
    >();

  tasks.forEach(
    (
      task,
    ) => {
      const deadline =
        new Date(
          task.deadline,
        );

      if (
        Number.isNaN(
          deadline.getTime(),
        )
      ) {
        return;
      }

      const key =
        localDateKey(
          deadline,
        );

      const current =
        result.get(
          key,
        ) ??
        [];

      current.push(
        task,
      );

      result.set(
        key,
        current,
      );
    },
  );

  result.forEach(
    (
      items,
    ) => {
      items.sort(
        (
          first,
          second,
        ) =>
          new Date(
            first.deadline,
          ).getTime() -
          new Date(
            second.deadline,
          ).getTime(),
      );
    },
  );

  return result;
}

export function formatCalendarTime(
  value: string,
): string {
  const date =
    new Date(
      value,
    );

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return value;
  }

  return new Intl.DateTimeFormat(
    undefined,
    {
      hour:
        "numeric",

      minute:
        "2-digit",
    },
  ).format(
    date,
  );
}

export function formatWeekRange(
  weekDays: Date[],
): string {
  const first =
    weekDays[
      0
    ];

  const last =
    weekDays[
      weekDays.length -
        1
    ];

  if (
    !first ||
    !last
  ) {
    return "";
  }

  const sameYear =
    first.getFullYear() ===
    last.getFullYear();

  const firstFormatter =
    new Intl.DateTimeFormat(
      undefined,
      {
        month:
          "short",

        day:
          "numeric",

        ...(sameYear
          ? {}
          : {
              year:
                "numeric" as const,
            }),
      },
    );

  const lastFormatter =
    new Intl.DateTimeFormat(
      undefined,
      {
        month:
          "short",

        day:
          "numeric",

        year:
          "numeric",
      },
    );

  return `${firstFormatter.format(
    first,
  )} – ${lastFormatter.format(
    last,
  )}`;
}

export function formatMonthLabel(
  value: Date,
): string {
  return new Intl.DateTimeFormat(
    undefined,
    {
      month:
        "long",

      year:
        "numeric",
    },
  ).format(
    value,
  );
}