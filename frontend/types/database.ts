export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  // Allows to automatically instantiate createClient with right options
  // instead of createClient<Database, { PostgrestVersion: 'XX' }>(URL, KEY)
  __InternalSupabase: {
    PostgrestVersion: "14.5"
  }
  public: {
    Tables: {
      academic_tasks: {
        Row: {
          created_at: string
          deadline: string
          description: string | null
          difficulty: string
          estimated_minutes: number
          id: string
          output_type: string
          status: string
          subject_id: string
          task_type: string
          title: string
          updated_at: string
          user_id: string
        }
        Insert: {
          created_at?: string
          deadline: string
          description?: string | null
          difficulty: string
          estimated_minutes: number
          id?: string
          output_type?: string
          status?: string
          subject_id: string
          task_type: string
          title: string
          updated_at?: string
          user_id?: string
        }
        Update: {
          created_at?: string
          deadline?: string
          description?: string | null
          difficulty?: string
          estimated_minutes?: number
          id?: string
          output_type?: string
          status?: string
          subject_id?: string
          task_type?: string
          title?: string
          updated_at?: string
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "academic_tasks_subject_id_fkey"
            columns: ["subject_id"]
            isOneToOne: false
            referencedRelation: "subjects"
            referencedColumns: ["id"]
          },
        ]
      }
      file_processing_jobs: {
        Row: {
          attempt_count: number
          completed_at: string | null
          created_at: string
          error_code: string | null
          error_message: string | null
          id: string
          started_at: string | null
          status: string
          study_file_id: string
          updated_at: string
          user_id: string
        }
        Insert: {
          attempt_count?: number
          completed_at?: string | null
          created_at?: string
          error_code?: string | null
          error_message?: string | null
          id?: string
          started_at?: string | null
          status?: string
          study_file_id: string
          updated_at?: string
          user_id: string
        }
        Update: {
          attempt_count?: number
          completed_at?: string | null
          created_at?: string
          error_code?: string | null
          error_message?: string | null
          id?: string
          started_at?: string | null
          status?: string
          study_file_id?: string
          updated_at?: string
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "file_processing_jobs_study_file_id_fkey"
            columns: ["study_file_id"]
            isOneToOne: true
            referencedRelation: "study_files"
            referencedColumns: ["id"]
          },
        ]
      }
      flashcard_decks: {
        Row: {
          created_at: string
          generated_at: string
          generation_count: number
          generation_model: string
          id: string
          requested_card_count: number
          scope_type: string
          sources: Json
          study_file_id: string | null
          subject_id: string
          title: string
          updated_at: string
          user_id: string
        }
        Insert: {
          created_at?: string
          generated_at?: string
          generation_count?: number
          generation_model: string
          id?: string
          requested_card_count: number
          scope_type: string
          sources?: Json
          study_file_id?: string | null
          subject_id: string
          title: string
          updated_at?: string
          user_id: string
        }
        Update: {
          created_at?: string
          generated_at?: string
          generation_count?: number
          generation_model?: string
          id?: string
          requested_card_count?: number
          scope_type?: string
          sources?: Json
          study_file_id?: string | null
          subject_id?: string
          title?: string
          updated_at?: string
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "flashcard_decks_study_file_id_fkey"
            columns: ["study_file_id"]
            isOneToOne: false
            referencedRelation: "study_files"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "flashcard_decks_subject_id_fkey"
            columns: ["subject_id"]
            isOneToOne: false
            referencedRelation: "subjects"
            referencedColumns: ["id"]
          },
        ]
      }
      flashcard_review_events: {
        Row: {
          card_position: number
          created_at: string
          deck_id: string
          id: string
          outcome: string
          reviewed_at: string
          user_id: string
        }
        Insert: {
          card_position: number
          created_at?: string
          deck_id: string
          id?: string
          outcome: string
          reviewed_at?: string
          user_id: string
        }
        Update: {
          card_position?: number
          created_at?: string
          deck_id?: string
          id?: string
          outcome?: string
          reviewed_at?: string
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "flashcard_review_events_deck_id_fkey"
            columns: ["deck_id"]
            isOneToOne: false
            referencedRelation: "flashcard_decks"
            referencedColumns: ["id"]
          },
        ]
      }
      flashcards: {
        Row: {
          answer: string
          created_at: string
          deck_id: string
          id: string
          position: number
          question: string
        }
        Insert: {
          answer: string
          created_at?: string
          deck_id: string
          id?: string
          position: number
          question: string
        }
        Update: {
          answer?: string
          created_at?: string
          deck_id?: string
          id?: string
          position?: number
          question?: string
        }
        Relationships: [
          {
            foreignKeyName: "flashcards_deck_id_fkey"
            columns: ["deck_id"]
            isOneToOne: false
            referencedRelation: "flashcard_decks"
            referencedColumns: ["id"]
          },
        ]
      }
      learning_output_confidences: {
        Row: {
          confidence_level: number
          created_at: string
          id: string
          output_type: string
          updated_at: string
          user_id: string
        }
        Insert: {
          confidence_level: number
          created_at?: string
          id?: string
          output_type: string
          updated_at?: string
          user_id: string
        }
        Update: {
          confidence_level?: number
          created_at?: string
          id?: string
          output_type?: string
          updated_at?: string
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "learning_output_confidences_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
        ]
      }
      learning_profile_subjects: {
        Row: {
          confidence_level: number
          created_at: string
          id: string
          subject_name: string
          subject_strength: string
          updated_at: string
          user_id: string
        }
        Insert: {
          confidence_level: number
          created_at?: string
          id?: string
          subject_name: string
          subject_strength: string
          updated_at?: string
          user_id: string
        }
        Update: {
          confidence_level?: number
          created_at?: string
          id?: string
          subject_name?: string
          subject_strength?: string
          updated_at?: string
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "learning_profile_subjects_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
        ]
      }
      learning_profiles: {
        Row: {
          common_study_challenges: string[]
          created_at: string
          estimated_task_completion_minutes: number | null
          preferred_learning_methods: string[]
          preferred_study_duration_minutes: number | null
          preferred_study_times: string[]
          updated_at: string
          user_id: string
        }
        Insert: {
          common_study_challenges?: string[]
          created_at?: string
          estimated_task_completion_minutes?: number | null
          preferred_learning_methods?: string[]
          preferred_study_duration_minutes?: number | null
          preferred_study_times?: string[]
          updated_at?: string
          user_id: string
        }
        Update: {
          common_study_challenges?: string[]
          created_at?: string
          estimated_task_completion_minutes?: number | null
          preferred_learning_methods?: string[]
          preferred_study_duration_minutes?: number | null
          preferred_study_times?: string[]
          updated_at?: string
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "learning_profiles_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: true
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
        ]
      }
      profiles: {
        Row: {
          avatar_url: string | null
          created_at: string
          full_name: string
          id: string
          onboarding_completed: boolean
          onboarding_completed_at: string | null
          onboarding_current_step: number
          program_name: string | null
          school_name: string | null
          timezone: string
          updated_at: string
          year_level: string | null
        }
        Insert: {
          avatar_url?: string | null
          created_at?: string
          full_name?: string
          id: string
          onboarding_completed?: boolean
          onboarding_completed_at?: string | null
          onboarding_current_step?: number
          program_name?: string | null
          school_name?: string | null
          timezone?: string
          updated_at?: string
          year_level?: string | null
        }
        Update: {
          avatar_url?: string | null
          created_at?: string
          full_name?: string
          id?: string
          onboarding_completed?: boolean
          onboarding_completed_at?: string | null
          onboarding_current_step?: number
          program_name?: string | null
          school_name?: string | null
          timezone?: string
          updated_at?: string
          year_level?: string | null
        }
        Relationships: []
      }
      quiz_attempt_answers: {
        Row: {
          answered_at: string
          attempt_id: string
          created_at: string
          id: string
          is_correct: boolean
          position: number
          question_type: string
          quiz_question_id: string
          submitted_answer: string
          topic: string
        }
        Insert: {
          answered_at?: string
          attempt_id: string
          created_at?: string
          id?: string
          is_correct: boolean
          position: number
          question_type: string
          quiz_question_id: string
          submitted_answer: string
          topic: string
        }
        Update: {
          answered_at?: string
          attempt_id?: string
          created_at?: string
          id?: string
          is_correct?: boolean
          position?: number
          question_type?: string
          quiz_question_id?: string
          submitted_answer?: string
          topic?: string
        }
        Relationships: [
          {
            foreignKeyName: "quiz_attempt_answers_attempt_id_fkey"
            columns: ["attempt_id"]
            isOneToOne: false
            referencedRelation: "quiz_attempts"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "quiz_attempt_answers_quiz_question_id_fkey"
            columns: ["quiz_question_id"]
            isOneToOne: false
            referencedRelation: "quiz_questions"
            referencedColumns: ["id"]
          },
        ]
      }
      quiz_attempts: {
        Row: {
          completed_at: string | null
          correct_count: number
          created_at: string
          current_position: number
          id: string
          question_count: number
          quiz_id: string
          score_percentage: number
          started_at: string
          status: string
          updated_at: string
          user_id: string
        }
        Insert: {
          completed_at?: string | null
          correct_count?: number
          created_at?: string
          current_position?: number
          id?: string
          question_count: number
          quiz_id: string
          score_percentage?: number
          started_at?: string
          status?: string
          updated_at?: string
          user_id: string
        }
        Update: {
          completed_at?: string | null
          correct_count?: number
          created_at?: string
          current_position?: number
          id?: string
          question_count?: number
          quiz_id?: string
          score_percentage?: number
          started_at?: string
          status?: string
          updated_at?: string
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "quiz_attempts_quiz_id_fkey"
            columns: ["quiz_id"]
            isOneToOne: false
            referencedRelation: "quizzes"
            referencedColumns: ["id"]
          },
        ]
      }
      quiz_questions: {
        Row: {
          accepted_answers: Json
          choices: Json
          correct_answer: string
          created_at: string
          explanation: string
          id: string
          position: number
          question: string
          question_type: string
          quiz_id: string
          topic: string
          updated_at: string
        }
        Insert: {
          accepted_answers?: Json
          choices?: Json
          correct_answer: string
          created_at?: string
          explanation: string
          id?: string
          position: number
          question: string
          question_type: string
          quiz_id: string
          topic: string
          updated_at?: string
        }
        Update: {
          accepted_answers?: Json
          choices?: Json
          correct_answer?: string
          created_at?: string
          explanation?: string
          id?: string
          position?: number
          question?: string
          question_type?: string
          quiz_id?: string
          topic?: string
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: "quiz_questions_quiz_id_fkey"
            columns: ["quiz_id"]
            isOneToOne: false
            referencedRelation: "quizzes"
            referencedColumns: ["id"]
          },
        ]
      }
      quizzes: {
        Row: {
          created_at: string
          difficulty: string
          generated_at: string
          generation_count: number
          generation_model: string
          id: string
          question_count: number
          quiz_type: string
          scope_type: string
          study_file_id: string | null
          subject_id: string
          title: string
          updated_at: string
          user_id: string
        }
        Insert: {
          created_at?: string
          difficulty: string
          generated_at?: string
          generation_count?: number
          generation_model: string
          id?: string
          question_count: number
          quiz_type: string
          scope_type: string
          study_file_id?: string | null
          subject_id: string
          title: string
          updated_at?: string
          user_id: string
        }
        Update: {
          created_at?: string
          difficulty?: string
          generated_at?: string
          generation_count?: number
          generation_model?: string
          id?: string
          question_count?: number
          quiz_type?: string
          scope_type?: string
          study_file_id?: string | null
          subject_id?: string
          title?: string
          updated_at?: string
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "quizzes_study_file_id_fkey"
            columns: ["study_file_id"]
            isOneToOne: false
            referencedRelation: "study_files"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "quizzes_subject_id_fkey"
            columns: ["subject_id"]
            isOneToOne: false
            referencedRelation: "subjects"
            referencedColumns: ["id"]
          },
        ]
      }
      reviewers: {
        Row: {
          content: Json
          created_at: string
          generated_at: string
          generation_count: number
          generation_model: string
          id: string
          reviewer_length: string
          scope_type: string
          sources: Json
          study_file_id: string | null
          subject_id: string
          title: string
          updated_at: string
          user_id: string
        }
        Insert: {
          content: Json
          created_at?: string
          generated_at?: string
          generation_count?: number
          generation_model: string
          id?: string
          reviewer_length: string
          scope_type: string
          sources?: Json
          study_file_id?: string | null
          subject_id: string
          title: string
          updated_at?: string
          user_id: string
        }
        Update: {
          content?: Json
          created_at?: string
          generated_at?: string
          generation_count?: number
          generation_model?: string
          id?: string
          reviewer_length?: string
          scope_type?: string
          sources?: Json
          study_file_id?: string | null
          subject_id?: string
          title?: string
          updated_at?: string
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "reviewers_study_file_id_fkey"
            columns: ["study_file_id"]
            isOneToOne: false
            referencedRelation: "study_files"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "reviewers_subject_id_fkey"
            columns: ["subject_id"]
            isOneToOne: false
            referencedRelation: "subjects"
            referencedColumns: ["id"]
          },
        ]
      }
      study_availability: {
        Row: {
          created_at: string
          day_of_week: number
          end_time: string
          id: string
          start_time: string
          updated_at: string
          user_id: string
        }
        Insert: {
          created_at?: string
          day_of_week: number
          end_time: string
          id?: string
          start_time: string
          updated_at?: string
          user_id: string
        }
        Update: {
          created_at?: string
          day_of_week?: number
          end_time?: string
          id?: string
          start_time?: string
          updated_at?: string
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "study_availability_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
        ]
      }
      study_conversations: {
        Row: {
          created_at: string
          id: string
          last_message_at: string
          study_file_id: string | null
          subject_id: string | null
          summarized_message_count: number
          summary_text: string | null
          summary_updated_at: string | null
          summary_version: number
          title: string
          updated_at: string
          user_id: string
        }
        Insert: {
          created_at?: string
          id?: string
          last_message_at?: string
          study_file_id?: string | null
          subject_id?: string | null
          summarized_message_count?: number
          summary_text?: string | null
          summary_updated_at?: string | null
          summary_version?: number
          title?: string
          updated_at?: string
          user_id: string
        }
        Update: {
          created_at?: string
          id?: string
          last_message_at?: string
          study_file_id?: string | null
          subject_id?: string | null
          summarized_message_count?: number
          summary_text?: string | null
          summary_updated_at?: string | null
          summary_version?: number
          title?: string
          updated_at?: string
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "study_conversations_study_file_id_fkey"
            columns: ["study_file_id"]
            isOneToOne: false
            referencedRelation: "study_files"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "study_conversations_subject_id_fkey"
            columns: ["subject_id"]
            isOneToOne: false
            referencedRelation: "subjects"
            referencedColumns: ["id"]
          },
        ]
      }
      study_file_ai_chunks: {
        Row: {
          chunk_index: number
          chunk_metadata: Json
          content: string
          created_at: string
          embedding: string
          embedding_dimensions: number
          embedding_model: string
          embedding_task_type: string
          end_offset: number
          id: string
          source_name: string | null
          start_offset: number
          study_file_id: string
          updated_at: string
          user_id: string
        }
        Insert: {
          chunk_index: number
          chunk_metadata?: Json
          content: string
          created_at?: string
          embedding: string
          embedding_dimensions?: number
          embedding_model: string
          embedding_task_type?: string
          end_offset: number
          id?: string
          source_name?: string | null
          start_offset: number
          study_file_id: string
          updated_at?: string
          user_id: string
        }
        Update: {
          chunk_index?: number
          chunk_metadata?: Json
          content?: string
          created_at?: string
          embedding?: string
          embedding_dimensions?: number
          embedding_model?: string
          embedding_task_type?: string
          end_offset?: number
          id?: string
          source_name?: string | null
          start_offset?: number
          study_file_id?: string
          updated_at?: string
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "study_file_ai_chunks_study_file_id_fkey"
            columns: ["study_file_id"]
            isOneToOne: false
            referencedRelation: "study_files"
            referencedColumns: ["id"]
          },
        ]
      }
      study_file_chunks: {
        Row: {
          chunk_index: number
          chunk_metadata: Json
          content: string
          created_at: string
          id: string
          locator_label: string | null
          locator_type: string | null
          study_file_id: string
          token_count: number | null
          user_id: string
        }
        Insert: {
          chunk_index: number
          chunk_metadata?: Json
          content: string
          created_at?: string
          id?: string
          locator_label?: string | null
          locator_type?: string | null
          study_file_id: string
          token_count?: number | null
          user_id: string
        }
        Update: {
          chunk_index?: number
          chunk_metadata?: Json
          content?: string
          created_at?: string
          id?: string
          locator_label?: string | null
          locator_type?: string | null
          study_file_id?: string
          token_count?: number | null
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "study_file_chunks_study_file_id_fkey"
            columns: ["study_file_id"]
            isOneToOne: false
            referencedRelation: "study_files"
            referencedColumns: ["id"]
          },
        ]
      }
      study_file_contents: {
        Row: {
          character_count: number
          created_at: string
          extracted_text: string
          extraction_metadata: Json
          id: string
          page_count: number | null
          sheet_count: number | null
          slide_count: number | null
          study_file_id: string
          updated_at: string
          user_id: string
        }
        Insert: {
          character_count?: number
          created_at?: string
          extracted_text?: string
          extraction_metadata?: Json
          id?: string
          page_count?: number | null
          sheet_count?: number | null
          slide_count?: number | null
          study_file_id: string
          updated_at?: string
          user_id: string
        }
        Update: {
          character_count?: number
          created_at?: string
          extracted_text?: string
          extraction_metadata?: Json
          id?: string
          page_count?: number | null
          sheet_count?: number | null
          slide_count?: number | null
          study_file_id?: string
          updated_at?: string
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "study_file_contents_study_file_id_fkey"
            columns: ["study_file_id"]
            isOneToOne: true
            referencedRelation: "study_files"
            referencedColumns: ["id"]
          },
        ]
      }
      study_files: {
        Row: {
          created_at: string
          failure_code: string | null
          failure_message: string | null
          id: string
          mime_type: string
          original_filename: string
          processed_at: string | null
          processing_status: string
          size_bytes: number
          storage_path: string
          subject_id: string
          topic: string
          updated_at: string
          user_id: string
        }
        Insert: {
          created_at?: string
          failure_code?: string | null
          failure_message?: string | null
          id?: string
          mime_type: string
          original_filename: string
          processed_at?: string | null
          processing_status?: string
          size_bytes: number
          storage_path: string
          subject_id: string
          topic: string
          updated_at?: string
          user_id: string
        }
        Update: {
          created_at?: string
          failure_code?: string | null
          failure_message?: string | null
          id?: string
          mime_type?: string
          original_filename?: string
          processed_at?: string | null
          processing_status?: string
          size_bytes?: number
          storage_path?: string
          subject_id?: string
          topic?: string
          updated_at?: string
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "study_files_subject_owner_fk"
            columns: ["subject_id", "user_id"]
            isOneToOne: false
            referencedRelation: "subjects"
            referencedColumns: ["id", "user_id"]
          },
        ]
      }
      study_messages: {
        Row: {
          content: string
          conversation_id: string
          created_at: string
          id: string
          outcome: string | null
          role: string
          sources: Json
        }
        Insert: {
          content: string
          conversation_id: string
          created_at?: string
          id?: string
          outcome?: string | null
          role: string
          sources?: Json
        }
        Update: {
          content?: string
          conversation_id?: string
          created_at?: string
          id?: string
          outcome?: string | null
          role?: string
          sources?: Json
        }
        Relationships: [
          {
            foreignKeyName: "study_messages_conversation_id_fkey"
            columns: ["conversation_id"]
            isOneToOne: false
            referencedRelation: "study_conversations"
            referencedColumns: ["id"]
          },
        ]
      }
      study_plans: {
        Row: {
          created_at: string
          ends_on: string
          generated_at: string | null
          generation_mode: string
          id: string
          starts_on: string
          status: string
          title: string
          updated_at: string
          user_id: string
        }
        Insert: {
          created_at?: string
          ends_on: string
          generated_at?: string | null
          generation_mode?: string
          id?: string
          starts_on: string
          status?: string
          title: string
          updated_at?: string
          user_id: string
        }
        Update: {
          created_at?: string
          ends_on?: string
          generated_at?: string | null
          generation_mode?: string
          id?: string
          starts_on?: string
          status?: string
          title?: string
          updated_at?: string
          user_id?: string
        }
        Relationships: []
      }
      study_sessions: {
        Row: {
          created_at: string
          ends_at: string
          id: string
          notes: string | null
          origin: string
          starts_at: string
          status: string
          study_plan_id: string
          subject_id: string
          title: string
          updated_at: string
          user_id: string
        }
        Insert: {
          created_at?: string
          ends_at: string
          id?: string
          notes?: string | null
          origin?: string
          starts_at: string
          status?: string
          study_plan_id: string
          subject_id: string
          title: string
          updated_at?: string
          user_id: string
        }
        Update: {
          created_at?: string
          ends_at?: string
          id?: string
          notes?: string | null
          origin?: string
          starts_at?: string
          status?: string
          study_plan_id?: string
          subject_id?: string
          title?: string
          updated_at?: string
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "study_sessions_plan_owner_fk"
            columns: ["study_plan_id", "user_id"]
            isOneToOne: false
            referencedRelation: "study_plans"
            referencedColumns: ["id", "user_id"]
          },
          {
            foreignKeyName: "study_sessions_subject_owner_fk"
            columns: ["subject_id", "user_id"]
            isOneToOne: false
            referencedRelation: "subjects"
            referencedColumns: ["id", "user_id"]
          },
        ]
      }
      subjects: {
        Row: {
          color: string
          created_at: string
          id: string
          name: string
          updated_at: string
          user_id: string
        }
        Insert: {
          color?: string
          created_at?: string
          id?: string
          name: string
          updated_at?: string
          user_id: string
        }
        Update: {
          color?: string
          created_at?: string
          id?: string
          name?: string
          updated_at?: string
          user_id?: string
        }
        Relationships: []
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      claim_next_file_processing_job: {
        Args: never
        Returns: {
          processing_job_id: string
          study_file_id: string
        }[]
      }
      complete_learning_profile_onboarding: { Args: never; Returns: boolean }
      complete_study_file_processing: {
        Args: {
          p_character_count: number
          p_chunks: Json
          p_extracted_text: string
          p_extraction_metadata: Json
          p_page_count: number
          p_sheet_count: number
          p_slide_count: number
          p_study_file_id: string
        }
        Returns: undefined
      }
      create_flashcard_deck_with_cards: {
        Args: {
          p_cards: Json
          p_generation_model: string
          p_requested_card_count: number
          p_scope_type: string
          p_sources: Json
          p_study_file_id: string
          p_subject_id: string
          p_title: string
          p_user_id: string
        }
        Returns: string
      }
      create_quiz_with_questions: {
        Args: {
          p_difficulty: string
          p_generation_model: string
          p_question_count: number
          p_questions: Json
          p_quiz_type: string
          p_scope_type: string
          p_study_file_id: string
          p_subject_id: string
          p_title: string
          p_user_id: string
        }
        Returns: string
      }
      fail_study_file_processing: {
        Args: {
          p_error_code: string
          p_error_message: string
          p_study_file_id: string
        }
        Returns: undefined
      }
      mark_study_file_indexing: {
        Args: { p_study_file_id: string }
        Returns: undefined
      }
      queue_study_file_processing: {
        Args: { p_study_file_id: string }
        Returns: {
          created_at: string
          failure_code: string | null
          failure_message: string | null
          id: string
          mime_type: string
          original_filename: string
          processed_at: string | null
          processing_status: string
          size_bytes: number
          storage_path: string
          subject_id: string
          topic: string
          updated_at: string
          user_id: string
        }[]
        SetofOptions: {
          from: "*"
          to: "study_files"
          isOneToOne: false
          isSetofReturn: true
        }
      }
      recover_stale_file_processing_jobs: {
        Args: { p_max_attempts?: number; p_stale_after_minutes?: number }
        Returns: {
          failed_count: number
          requeued_count: number
        }[]
      }
      replace_generated_study_plan_sessions: {
        Args: {
          p_generated_at: string
          p_sessions: Json
          p_study_plan_id: string
          p_user_id: string
        }
        Returns: {
          plan: Json
          sessions: Json
        }[]
      }
      replace_learning_output_confidences: {
        Args: { p_confidences: Json }
        Returns: undefined
      }
      replace_learning_profile_subjects: {
        Args: { p_subjects: Json }
        Returns: undefined
      }
      replace_study_availability: {
        Args: { p_slots: Json }
        Returns: undefined
      }
      replace_study_file_ai_chunks: {
        Args: {
          p_chunks: Json
          p_embedding_dimensions: number
          p_embedding_model: string
          p_original_character_count: number
          p_study_file_id: string
        }
        Returns: number
      }
      search_study_file_ai_chunks: {
        Args: {
          p_match_count?: number
          p_query_embedding: Json
          p_similarity_threshold?: number
          p_study_file_id?: string
          p_subject_id?: string
          p_user_id: string
        }
        Returns: {
          chunk_id: string
          chunk_index: number
          chunk_metadata: Json
          content: string
          embedding_model: string
          end_offset: number
          similarity_score: number
          source_name: string
          start_offset: number
          study_file_id: string
          subject_id: string
        }[]
      }
      start_quiz_attempt: {
        Args: { p_quiz_id: string; p_user_id: string }
        Returns: {
          completed_at: string
          correct_count: number
          created_at: string
          current_position: number
          id: string
          question_count: number
          quiz_id: string
          score_percentage: number
          started_at: string
          status: string
          updated_at: string
        }[]
      }
      start_study_file_processing: {
        Args: { p_study_file_id: string }
        Returns: undefined
      }
      submit_quiz_attempt_answer: {
        Args: {
          p_attempt_id: string
          p_position: number
          p_submitted_answer: string
          p_user_id: string
        }
        Returns: {
          answered_position: number
          attempt_completed: boolean
          attempt_id: string
          completed_at: string
          correct_answer: string
          correct_count: number
          created_at: string
          current_position: number
          explanation: string
          is_correct: boolean
          next_position: number
          question_count: number
          quiz_id: string
          quiz_question_id: string
          score_percentage: number
          started_at: string
          status: string
          updated_at: string
        }[]
      }
    }
    Enums: {
      [_ in never]: never
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

type DatabaseWithoutInternals = Omit<Database, "__InternalSupabase">

type DefaultSchema = DatabaseWithoutInternals[Extract<keyof Database, "public">]

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
        DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
      DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema["Tables"] &
        DefaultSchema["Views"])
    ? (DefaultSchema["Tables"] &
        DefaultSchema["Views"])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R
      }
      ? R
      : never
    : never

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I
      }
      ? I
      : never
    : never

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U
      }
      ? U
      : never
    : never

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema["Enums"]
    | { schema: keyof DatabaseWithoutInternals },
  EnumName extends DefaultSchemaEnumNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"]
    : never = never,
> = DefaultSchemaEnumNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema["Enums"]
    ? DefaultSchema["Enums"][DefaultSchemaEnumNameOrOptions]
    : never

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema["CompositeTypes"]
    | { schema: keyof DatabaseWithoutInternals },
  CompositeTypeName extends PublicCompositeTypeNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never = never,
> = PublicCompositeTypeNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema["CompositeTypes"]
    ? DefaultSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never

export const Constants = {
  public: {
    Enums: {},
  },
} as const
