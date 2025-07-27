# frozen_string_literal: true

module Types
  module Analytics
    module AiUsage
      # rubocop:disable Graphql/AuthorizeTypes -- authorized in parent type.
      class AiUsageEventType < BaseObject
        graphql_name 'AiUsageEvent'

        field :id,
          GraphQL::Types::ID,
          null: false,
          description: "ID of the code suggestion event."

        field :timestamp,
          Types::TimeType,
          null: false,
          description: 'When the event happened.'

        field :event,
          AiUsageEventTypeEnum,
          null: false,
          description: 'Type of the event.'

        field :user,
          Types::UserType,
          null: false,
          description: 'User associated with the event.'

        def user
          Gitlab::Graphql::Loaders::BatchModelLoader.new(User, object.user_id).find
        end
      end
      # rubocop:enable Graphql/AuthorizeTypes
    end
  end
end
