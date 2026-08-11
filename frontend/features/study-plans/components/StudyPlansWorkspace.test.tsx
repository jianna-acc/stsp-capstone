// File: /frontend/features/study-plans/components/StudyPlansWorkspace.test.tsx
// Purpose: Tests Track D study-plan loading, session calendar
// rendering, and saved-plan switching.

import {
  MantineProvider,
} from "@mantine/core";
import {
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import type {
  SubjectSummary,
} from "@/features/subjects/types";


const apiMocks =
  vi.hoisted(
    () => ({
      createStudyPlan:
        vi.fn(),
      createStudySession:
        vi.fn(),
      deleteStudyPlan:
        vi.fn(),
      deleteStudySession:
        vi.fn(),
      generateStudyPlan:
      vi.fn(),
      regenerateStudyPlan:
      vi.fn(),
      listStudyPlans:
      vi.fn(),
      listStudySessions:
        vi.fn(),
    }),
  );


vi.mock(
  "../api",
  () =>
    apiMocks,
);

const academicTaskApiMocks =
  vi.hoisted(
    () => ({
      listPrioritizedAcademicTasks:
        vi.fn(),
    }),
  );


vi.mock(
  "@/features/academic-tasks/api",
  () =>
    academicTaskApiMocks,
);

import {
  StudyPlansWorkspace,
} from "./StudyPlansWorkspace";


const SUBJECTS = [
  {
    id: "biology-subject",
    name: "Biology",
    color: "green",
    created_at:
      "2026-08-01T08:00:00Z",
    updated_at:
      "2026-08-01T08:00:00Z",
  },
  {
    id: "history-subject",
    name: "History",
    color: "orange",
    created_at:
      "2026-08-01T08:00:00Z",
    updated_at:
      "2026-08-01T08:00:00Z",
  },
] as SubjectSummary[];


const PLANS = [
  {
    id: "finals-plan",
    title: "Finals Plan",
    starts_on: "2026-08-10",
    ends_on: "2026-08-16",
    status: "active",
    generation_mode: "manual",
    generated_at: null,
    created_at:
      "2026-08-10T08:00:00Z",
    updated_at:
      "2026-08-10T08:00:00Z",
  },
  {
    id: "research-plan",
    title: "Research Plan",
    starts_on: "2026-08-17",
    ends_on: "2026-08-23",
    status: "active",
    generation_mode: "generated",
    generated_at:
      "2026-08-10T08:00:00Z",
    created_at:
      "2026-08-10T08:00:00Z",
    updated_at:
      "2026-08-10T08:00:00Z",
  },
] as const;


const FINALS_SESSIONS = [
  {
    id: "biology-session",
    study_plan_id:
      "finals-plan",
    subject_id:
      "biology-subject",
    title:
      "Review Chapter 4",
    starts_at:
      "2026-08-10T18:00:00+08:00",
    ends_at:
      "2026-08-10T19:00:00+08:00",
    status: "planned",
    origin: "manual",
    notes: null,
    created_at:
      "2026-08-10T08:00:00Z",
    updated_at:
      "2026-08-10T08:00:00Z",
  },
] as const;


const RESEARCH_SESSIONS = [
  {
    id: "history-session",
    study_plan_id:
      "research-plan",
    subject_id:
      "history-subject",
    title:
      "Draft research outline",
    starts_at:
      "2026-08-17T19:00:00+08:00",
    ends_at:
      "2026-08-17T20:00:00+08:00",
    status: "planned",
    origin: "generated",
    notes: null,
    created_at:
      "2026-08-10T08:00:00Z",
    updated_at:
      "2026-08-10T08:00:00Z",
  },
] as const;

const PRIORITIZED_TASKS = [
  {
    task: {
      id:
        "55555555-5555-4555-8555-555555555555",
      subject_id:
        "biology-subject",
      title:
        "Study for Biology exam",
      description:
        null,
      deadline:
        "2026-08-20T18:00:00+08:00",
      estimated_minutes:
        180,
      difficulty:
        "hard",
      task_type:
        "exam",
      output_type:
        "memorization",
      status:
        "pending",
      created_at:
        "2026-08-10T08:00:00Z",
      updated_at:
        "2026-08-10T08:00:00Z",
    },

    priority: {
      total_score:
        92,
      deadline_score:
        90,
      difficulty_score:
        100,
      estimated_time_score:
        60,
      output_confidence_score:
        50,
      previous_performance_score:
        50,
      available_study_time_score:
        50,
      status_score:
        50,
    },
  },

  {
    task: {
      id:
        "66666666-6666-4666-8666-666666666666",
      subject_id:
        "history-subject",
      title:
        "Completed History reading",
      description:
        null,
      deadline:
        "2026-08-19T18:00:00+08:00",
      estimated_minutes:
        60,
      difficulty:
        "easy",
      task_type:
        "reading",
      output_type:
        "reading_analysis",
      status:
        "completed",
      created_at:
        "2026-08-10T08:00:00Z",
      updated_at:
        "2026-08-10T08:00:00Z",
    },

    priority: {
      total_score:
        80,
      deadline_score:
        80,
      difficulty_score:
        40,
      estimated_time_score:
        30,
      output_confidence_score:
        50,
      previous_performance_score:
        50,
      available_study_time_score:
        50,
      status_score:
        0,
    },
  },
];


const GENERATED_RESULT = {
  plan: {
    id:
      "77777777-7777-4777-8777-777777777777",
    title:
      "Generated Finals Plan",
    starts_on:
      "2026-08-10",
    ends_on:
      "2026-08-20",
    status:
      "active",
    generation_mode:
      "generated",
    generated_at:
      "2026-08-10T15:00:00Z",
    created_at:
      "2026-08-10T15:00:00Z",
    updated_at:
      "2026-08-10T15:00:00Z",
  },

  sessions: [
    {
      id:
        "88888888-8888-4888-8888-888888888888",
      study_plan_id:
        "77777777-7777-4777-8777-777777777777",
      subject_id:
        "biology-subject",
      title:
        "Study for Biology exam",
      starts_at:
        "2026-08-11T18:00:00+08:00",
      ends_at:
        "2026-08-11T19:00:00+08:00",
      status:
        "planned",
      origin:
        "generated",
      notes:
        null,
      created_at:
        "2026-08-10T15:00:00Z",
      updated_at:
        "2026-08-10T15:00:00Z",
    },
  ],

  unscheduled_tasks:
    [],
} as const;

const REGENERATED_RESULT = {
  plan: {
    ...PLANS[1],
    generated_at:
      "2026-08-11T01:00:00Z",
    updated_at:
      "2026-08-11T01:00:00Z",
  },

  sessions: [
    {
      id:
        "regenerated-history-session",
      study_plan_id:
        "research-plan",
      subject_id:
        "biology-subject",
      title:
        "Study for Biology exam",
      starts_at:
        "2026-08-18T18:00:00+08:00",
      ends_at:
        "2026-08-18T19:00:00+08:00",
      status:
        "planned",
      origin:
        "generated",
      notes:
        null,
      created_at:
        "2026-08-11T01:00:00Z",
      updated_at:
        "2026-08-11T01:00:00Z",
    },
  ],

  unscheduled_tasks:
    [],
} as const;

function renderWorkspace() {
  return render(
    <MantineProvider>
      <StudyPlansWorkspace
        initialSubjects={
          SUBJECTS
        }
      />
    </MantineProvider>,
  );
}


describe(
  "StudyPlansWorkspace",
  () => {
    beforeEach(
      () => {
        apiMocks
          .listStudyPlans
          .mockReset()
          .mockResolvedValue(
            PLANS,
          );

        apiMocks
          .listStudySessions
          .mockReset()
          .mockImplementation(
            (
              planId:
                string,
            ) => {
              if (
                planId ===
                "research-plan"
              ) {
                return Promise.resolve(
                  RESEARCH_SESSIONS,
                );
              }

              return Promise.resolve(
                FINALS_SESSIONS,
              );
            },
          );
          apiMocks
            .generateStudyPlan
            .mockReset();

            academicTaskApiMocks
            .listPrioritizedAcademicTasks
            .mockReset()
            .mockResolvedValue(
                PRIORITIZED_TASKS,
            );
            apiMocks
                .regenerateStudyPlan
                .mockReset();
                    },
    );

    it(
      "loads saved plans and displays the selected plan sessions",
      async () => {
        renderWorkspace();

        expect(
          screen.getByLabelText(
            "Loading study plans",
          ),
        ).toBeInTheDocument();

        expect(
            await screen.findByRole(
                "heading",
                {
                name: "Finals Plan",
                level: 2,
                },
            ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Research Plan",
          ),
        ).toBeInTheDocument();

        expect(
          await screen.findByText(
            "Review Chapter 4",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "Biology",
          ),
        ).toBeInTheDocument();

        expect(
          apiMocks
            .listStudyPlans,
        ).toHaveBeenCalledWith(
          50,
          {
            signal:
              expect.any(
                AbortSignal,
              ),
          },
        );
      },
    );


    it(
      "switches plans and loads the selected schedule",
      async () => {
        const user =
          userEvent.setup();

        renderWorkspace();

        const researchPlan =
          await screen.findByRole(
            "button",
            {
              name:
                /Research Plan/i,
            },
          );

        await user.click(
          researchPlan,
        );

        expect(
          await screen.findByText(
            "Draft research outline",
          ),
        ).toBeInTheDocument();

        expect(
          screen.getByText(
            "History",
          ),
        ).toBeInTheDocument();

        await waitFor(
          () => {
            expect(
              apiMocks
                .listStudySessions,
            ).toHaveBeenCalledWith(
              "research-plan",
              200,
              {
                signal:
                  expect.any(
                    AbortSignal,
                  ),
              },
            );
          },
        );
      },
    );


    it(
      "shows the empty state when no plans exist",
      async () => {
        apiMocks
          .listStudyPlans
          .mockResolvedValue(
            [],
          );

        renderWorkspace();

        expect(
          await screen.findByText(
            "No study plans yet",
          ),
        ).toBeInTheDocument();

        expect(
          apiMocks
            .listStudySessions,
        ).not.toHaveBeenCalled();
      },
    );
    it(
        "generates a study plan from prioritized academic tasks",
        async () => {
            const user =
            userEvent.setup();

            apiMocks
            .generateStudyPlan
            .mockResolvedValue(
                GENERATED_RESULT,
            );

            apiMocks
            .listStudySessions
            .mockImplementation(
                (
                planId:
                    string,
                ) => {
                if (
                    planId ===
                    GENERATED_RESULT
                    .plan.id
                ) {
                    return Promise.resolve(
                    GENERATED_RESULT
                        .sessions,
                    );
                }

                if (
                    planId ===
                    "research-plan"
                ) {
                    return Promise.resolve(
                    RESEARCH_SESSIONS,
                    );
                }

                return Promise.resolve(
                    FINALS_SESSIONS,
                );
                },
            );

            renderWorkspace();

            await screen.findByRole(
            "heading",
            {
                name:
                "Finals Plan",
                level:
                2,
            },
            );

            await user.click(
            screen.getByRole(
                "button",
                {
                name:
                    /generate plan/i,
                },
            ),
            );

            await waitFor(
            () => {
                expect(
                academicTaskApiMocks
                    .listPrioritizedAcademicTasks,
                ).toHaveBeenCalledWith({
                limit:
                    100,
                });
            },
            );

            const dialog =
                await screen.findByRole(
                    "dialog",
                );

                expect(
                within(
                    dialog,
                ).getByText(
                    "Generate study plan",
                ),
                ).toBeInTheDocument();

            await user.type(
            within(
                dialog,
            ).getByLabelText(
                /plan title/i,
            ),
            "Generated Finals Plan",
            );

            await user.type(
            within(
                dialog,
            ).getByLabelText(
                /start date/i,
            ),
            "2026-08-10",
            );

            await user.type(
            within(
                dialog,
            ).getByLabelText(
                /end date/i,
            ),
            "2026-08-20",
            );

            await user.click(
            within(
                dialog,
            ).getByRole(
                "button",
                {
                name:
                    /generate plan/i,
                },
            ),
            );

            await waitFor(
            () => {
                expect(
                apiMocks
                    .generateStudyPlan,
                ).toHaveBeenCalledWith({
                title:
                    "Generated Finals Plan",
                starts_on:
                    "2026-08-10",
                ends_on:
                    "2026-08-20",
                tasks: [
                    {
                    task_id:
                        "55555555-5555-4555-8555-555555555555",
                    subject_id:
                        "biology-subject",
                    title:
                        "Study for Biology exam",
                    deadline:
                        "2026-08-20T18:00:00+08:00",
                    estimated_minutes:
                        180,
                    priority_weight:
                        5,
                    },
                ],
                });
            },
            );

            expect(
            await within(
                dialog,
            ).findByText(
                /1 study session was generated/i,
            ),
            ).toBeInTheDocument();

            await user.click(
            within(
                dialog,
            ).getByRole(
                "button",
                {
                name:
                    /done/i,
                },
            ),
            );

            expect(
            await screen.findByRole(
                "heading",
                {
                name:
                    "Generated Finals Plan",
                level:
                    2,
                },
            ),
            ).toBeInTheDocument();

            expect(
            await screen.findByText(
                "Study for Biology exam",
            ),
            ).toBeInTheDocument();
        },
        );
it(
  "regenerates an existing generated plan from latest academic tasks",
  async () => {
    const user =
      userEvent.setup();

    apiMocks
      .regenerateStudyPlan
      .mockResolvedValue(
        REGENERATED_RESULT,
      );

    renderWorkspace();

    await screen.findByRole(
      "heading",
      {
        name:
          "Finals Plan",
        level:
          2,
      },
    );

    expect(
      screen.queryByRole(
        "button",
        {
          name:
            /^regenerate$/i,
        },
      ),
    ).not.toBeInTheDocument();

    const researchPlan =
      screen.getByRole(
        "button",
        {
          name:
            /Research Plan/i,
        },
      );

    await user.click(
      researchPlan,
    );

    expect(
      await screen.findByText(
        "Draft research outline",
      ),
    ).toBeInTheDocument();

    const regenerateButton =
      screen.getByRole(
        "button",
        {
          name:
            /^regenerate$/i,
        },
      );

    await user.click(
      regenerateButton,
    );

    await waitFor(
      () => {
        expect(
          academicTaskApiMocks
            .listPrioritizedAcademicTasks,
        ).toHaveBeenCalledWith({
          limit:
            100,
        });
      },
    );

    const dialog =
      await screen.findByRole(
        "dialog",
      );

    expect(
      within(
        dialog,
      ).getByText(
        "Regenerate study plan",
      ),
    ).toBeInTheDocument();

    expect(
      within(
        dialog,
      ).getByText(
        /1 eligible task is currently available/i,
      ),
    ).toBeInTheDocument();

    await user.click(
      within(
        dialog,
      ).getByRole(
        "button",
        {
          name:
            /regenerate plan/i,
        },
      ),
    );

    await waitFor(
      () => {
        expect(
          apiMocks
            .regenerateStudyPlan,
        ).toHaveBeenCalledWith(
          "research-plan",
          {
            tasks: [
              {
                task_id:
                  "55555555-5555-4555-8555-555555555555",
                subject_id:
                  "biology-subject",
                title:
                  "Study for Biology exam",
                deadline:
                  "2026-08-20T18:00:00+08:00",
                estimated_minutes:
                  180,
                priority_weight:
                  5,
              },
            ],
          },
        );
      },
    );

    expect(
      await within(
        dialog,
      ).findByText(
        /study plan regenerated/i,
      ),
    ).toBeInTheDocument();

    await user.click(
      within(
        dialog,
      ).getByRole(
        "button",
        {
          name:
            /done/i,
        },
      ),
    );

    expect(
      await screen.findByRole(
        "heading",
        {
          name:
            "Research Plan",
          level:
            2,
        },
      ),
    ).toBeInTheDocument();

    expect(
      await screen.findByText(
        "Study for Biology exam",
      ),
    ).toBeInTheDocument();

    expect(
      screen.queryByText(
        "Draft research outline",
      ),
    ).not.toBeInTheDocument();
  },
);
  },
);